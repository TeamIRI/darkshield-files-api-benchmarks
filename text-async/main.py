import aiohttp
import asyncio
import argparse
import os
import json
import logging
import async_utils
import datetime

from setup import setup, teardown, file_mask_context_name, file_search_context_name


async def main(arguments):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0)) as session:
        try:
            await setup(session, arguments.buffer_limit)
            context = json.dumps({
                "fileSearchContextName": file_search_context_name,
                "fileMaskContextName": file_mask_context_name
            })
            print(datetime.datetime.now())
            queue = asyncio.Queue(arguments.workers)
            workers = [asyncio.create_task(async_utils.benchmark_search_mask_async(session, file_name, context,
                                                                                   arguments.lines, q, queue)) for q in
                       range(arguments.number_files)]
            file_datas = [file_data for _ in range(arguments.number_files)]
            for obj in file_datas:
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
            print(datetime.datetime.now())
            await teardown(session)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='Benchmark text file search/masking.')
    parser.add_argument('lines', type=int,
                        help='The number of text lines to create for the test file. Each line is 1kb in size.')
    parser.add_argument('-n', '--number-files', metavar='N', type=int, default=10,
                        help='The number of files to use. Defaults to 10.')
    parser.add_argument('-b', '--buffer-limit', metavar='N', type=int,
                        help='Set the buffer limit to use for the text file in memory-constrained environments.')
    parser.add_argument('-w', '--workers', metavar='N', type=int, default=4,
                        help=('The max number of workers to use to process the files. '
                              'The default number is 4.'))
    args = parser.parse_args()
    lines = args.lines
    buffer_limit = args.buffer_limit
    test_folder = 'test-files'
    file_name = f'test-{lines}.txt'
    file_path = f'{test_folder}/{file_name}'
    os.makedirs(test_folder, exist_ok=True)
    os.makedirs(f'results/{lines}', exist_ok=True)
    if not os.path.exists(file_path):
        logging.info(f'Creating {file_name}...')
        test_line = 'this is a test'
        line = '#' * (1000 - len(test_line) - len(os.linesep)) + test_line + os.linesep
        with open(file_path, 'w') as f:
            for i in range(lines):
                f.write(line)
        logging.info(f'Created {file_name}.')
    f_2 = open(file_path, 'r')
    file_data = f_2.read()
    asyncio.run(main(args))
