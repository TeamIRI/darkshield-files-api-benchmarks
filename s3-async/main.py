import aioboto3
import aiohttp
import asyncio
import argparse
import concurrent.futures
import json
import logging
import timeit

# from boto3.s3.transfer import TransferConfig

from setup import setup, teardown, file_mask_context_name, file_search_context_name

# A class that is used to decorate an aiohttp.PartReader to add the necessary 'read'
# method to conform to the interface for io.BinaryIO used in 'aioboto3.s3.upload_fileobj'.
class PartReader():
  
  def __init__(self, part):
    self.part = part

  async def read(self, chunk_size=8192):
    return await self.part.read_chunk(chunk_size)


# Used to stream the s3 object directly to the API without storing it all in memory or on file.
async def s3_object_sender(obj, chunk_size=8192):
  obj = await obj.get()
  async with obj['Body'] as stream:
    chunk = await stream.read(chunk_size)
    while chunk:
      yield chunk
      chunk = await stream.read(chunk_size)


async def main(bucket_name, prefix, profile_name):
  boto_session = aioboto3.session.Session(profile_name=profile_name)
  async with aiohttp.ClientSession() as session, boto_session.resource('s3') as s3:
    try:
      await setup(session)
      bucket = await s3.Bucket(bucket_name)
      url = 'http://localhost:8080/api/darkshield/files/fileSearchContext.mask'
      context = json.dumps({
        "fileSearchContextName": file_search_context_name,
        "fileMaskContextName": file_mask_context_name
      })
      if prefix:
        logging.info(f"Filtering on prefix '{prefix}'...")
        objects = bucket.objects.filter(Prefix=prefix)
      else:
        logging.info('Extracting all objects from bucket...')
        objects = bucket.objects.all()
      
      # TODO: USE THIS FOR PARALLEL processing.
      # sema = asyncio.BoundedSemaphore(5)
      async for obj in objects:
        file_name = obj.key
        await obj.load() # Load the metadata for this object.
        content_type = obj.meta.data.get('ContentType', 'application/octet-stream')
        logging.info('Processing "%s"...', file_name)
        logging.info('Content type: %s', content_type)
        if content_type.startswith('application/x-directory') or file_name.startswith('darkshield-masked'):
          logging.info('Skipping "%s"...', file_name)
        else:
          data = aiohttp.FormData()
          data.add_field('context', context,
                         filename='context',
                         content_type='application/json')
          data.add_field('file', s3_object_sender(obj),
                        filename=file_name,
                        content_type=content_type)
          logging.info('Sending request to API...')
          async with session.post(url, data=data) as r:
            if r.status >= 300:
              raise Exception(f"Failed with status {r.status}:\n\n{await r.json()}")
            
            logging.info('Processing response...')
            reader = aiohttp.MultipartReader.from_response(r)
            part = await reader.next()
            while part is not None:
              if part.name == 'file':
                target = f'darkshield-masked/{file_name}'
                logging.info('Uploading to "%s"...', target)
                await bucket.upload_fileobj(PartReader(part), target)

              part = await reader.next()
            
        logging.info('Processed "%s".', file_name)
    finally:
      await teardown(session)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='Benchmark for S3 bucket search/masking.')
    parser.add_argument('bucket', type=str, metavar='bucket_name_or_url', 
                        help="The name of the bucket, or the s3 url of the object (starting with 's3://').")
    parser.add_argument('-p', '--profile', metavar='name', type=str, 
                        help='The name of AWS profile to use for the connection (otherwise the default is used).')
    
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

    asyncio.run(main(bucket_name, prefix, args.profile))