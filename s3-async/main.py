import aioboto3
import aiohttp
import asyncio
import argparse
import json
import logging

from boto3.s3.transfer import TransferConfig

from setup import setup, teardown, file_mask_context_name, file_search_context_name
# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from server_config import hostname, port, is_https

host = f'http{"s" if is_https else ""}://{hostname}:{port}/api/darkshield'

# A class that is used to decorate an aiohttp.PartReader to add the necessary 'read'
# method to conform to the interface for io.BinaryIO used in 'aioboto3.s3.upload_fileobj'.
class PartReader():

  def __init__(self, part):
    self.part = part

  async def read(self, chunk_size):
    return await self.part.read_chunk(chunk_size)


# Used to stream the s3 object directly to the API without storing it all in memory or on file.
async def s3_object_sender(obj, chunk_size):
  obj = await obj.get()
  async with obj['Body'] as stream:
    chunk = await stream.read(chunk_size)
    while chunk:
      yield chunk
      chunk = await stream.read(chunk_size)


# An asyncio worker that processes s3 objects out of a queue.
async def s3_obj_worker(name, queue, session, bucket, context, chunk_size, no_results):
  url = f'{host}/files/fileSearchContext.mask'
  while True:
    obj = await queue.get()
    logging.info('%s: Starting task...', name)
    file_name = obj.key
    await obj.load() # Load the metadata for this object.
    content_type = obj.meta.data.get('ContentType', 'application/octet-stream')
    logging.info('%s: Processing "%s"...', name, file_name)
    logging.info('%s: Content type: %s', name, content_type)
    if content_type.startswith('application/x-directory')\
      or file_name.startswith('darkshield-masked')\
        or file_name.startswith('darkshield-results'):

      logging.info('%s: Skipping "%s"...', name, file_name)
    else:
      data = aiohttp.FormData()
      data.add_field('context', context,
                      filename='context',
                      content_type='application/json')
      data.add_field('file', s3_object_sender(obj, chunk_size),
                    filename=file_name,
                    content_type=content_type)
      logging.info('%s: Sending request to API...', name)
      async with session.post(url, data=data) as r:
        if r.status != 200:
          logging.error('%s: Failed to mask with error code %d: %s', 
                        name, r.status, await r.content.read())
        else:
          logging.info('%s: Processing response...', name)
          reader = aiohttp.MultipartReader.from_response(r)
          part = await reader.next()
          while part is not None:
            if part.name == 'file':
              target = f'darkshield-masked/{file_name}'
              logging.info('%s: Uploading to "%s"...', name, target)
              config = TransferConfig(
                multipart_threshold=chunk_size
              )
              await bucket.upload_fileobj(PartReader(part), target, Config=config)
            elif part.name == 'results' and not no_results:
              file_name = file_name.replace('.', '_')
              target = f'darkshield-results/{file_name}-results.json'
              logging.info('%s: Uploading to "%s"...', name, target)
              config = TransferConfig(
                multipart_threshold=chunk_size
              )
              await bucket.upload_fileobj(PartReader(part), target, Config=config)

            part = await reader.next()

        logging.info('%s: Processed "%s".', name, file_name)

    queue.task_done()
    logging.info('%s: Task completed.', name)


async def main(bucket_name, prefix, args):
  boto_session = aioboto3.session.Session(profile_name=args.profile)
  async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0)) as session,\
    boto_session.resource('s3') as s3:

    try:
      await setup(session, args.buffer_limit)
      bucket = await s3.Bucket(bucket_name)
      context = json.dumps({
        "fileSearchContextName": file_search_context_name,
        "fileMaskContextName": file_mask_context_name
      })
      queue = asyncio.Queue(args.workers)
      workers = [asyncio.create_task(s3_obj_worker(f'worker-{i}', queue, session,
                 bucket, context, args.chunk_size, args.no_results)) for i in range(args.workers)]
      logging.info('Created %d workers.', args.workers)

      if prefix:
        logging.info(f"Filtering on prefix '{prefix}'...")
        objects = bucket.objects.filter(Prefix=prefix)
      else:
        logging.info('Extracting all objects from bucket...')
        objects = bucket.objects.all()

      async for obj in objects:
        await queue.put(obj)
      
      # wait for either `queue.join()` to complete or a consumer to raise
      done, _ = await asyncio.wait([queue.join(), *workers],
                                    return_when=asyncio.FIRST_COMPLETED)

      error_raised = set(done) & set(workers)
      if error_raised:
        await error_raised.pop()  # propagate the exception

      logging.info('Stopping workers...')
      for worker in workers:
        worker.cancel()
    finally:
      await teardown(session)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='Benchmark for S3 bucket search/masking.')
    parser.add_argument('bucket', type=str, metavar='bucket_name_or_url', 
                        help="The name of the bucket, or the s3 url of the object (starting with 's3://').")
    parser.add_argument('-b', '--buffer-limit', metavar='N', type=int,
                        help='Set the buffer limit to use for text files in memory-constrained environments.')
    parser.add_argument('-c', '--chunk_size', type=int, metavar='N', default=8192,
                        help='The chunk size to use for communicating with S3 and the API. The default is 8192.')
    # parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, 
    #                     help='The number of times the test should be run to obtain the average. Defaults to 10.')
    parser.add_argument('--no-results', dest='no_results', action='store_true',
                        help='Disable the generation of results.json files.')
    parser.add_argument('-p', '--profile', metavar='name', type=str, 
                        help='The name of AWS profile to use for the connection (otherwise the default is used).')
    parser.add_argument('-w', '--workers', metavar='N', type=int, default=4,
                        help=('The max number of workers to use to process the files. '
                              'The default number is 4.'))

    args = parser.parse_args()
    bucket_name = args.bucket
    prefix = None
    if bucket_name.startswith('s3://'):
      logging.info('Parsing bucket url...')
      split = bucket_name[5:].split('/', 1)
      if len(split) == 2:
        bucket_name, prefix = split
        logging.info('Found bucket name "%s" and prefix "%s".', bucket_name, prefix)
      else:
        bucket_name = split[0]
        logging.info('Found bucket name "%s".', bucket_name)

    asyncio.run(main(bucket_name, prefix, args))
