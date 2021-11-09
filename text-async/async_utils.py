import logging
import os
import aiohttp
import aiofiles
import sys

# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from server_config import hostname, port, is_https

host = f'http{"s" if is_https else ""}://{hostname}:{port}/api/darkshield'



async def create_context(session, context, data):
    url = f'{host}/{context}.create'
    logging.info(f'POST: {url}')
    await session.post(url, json=data, raise_for_status=True)


async def destroy_context(session, context, name):
    url = f'{host}/{context}.destroy'
    logging.info(f'POST: {url}')
    await session.post(url, json={'name': name})


async def benchmark_search_mask_async(session, file_name, context, file_size, i,
                                      queue):
    logging.info(f': Task{i} started.')
    while True:
        folder_name = f'results/{file_size}'
        url = f'{host}/files/fileSearchContext.mask'
        os.makedirs(folder_name, exist_ok=True)
        f = await queue.get()
        data = aiohttp.FormData()
        data.add_field('context', context,
                       filename='context',
                       content_type='application/json')
        data.add_field('file', f,
                       filename=file_name,
                       content_type='text/plain')
        async with session.post(url, data=data) as r:
            if r.status >= 300:
                raise Exception(f"Failed with status {r.status}:\n\n{await r.json()}")
            reader = aiohttp.MultipartReader.from_response(r)
            part = await reader.next()
            file_response = await aiofiles.open(f'{file_name}_{i}', 'wb')
            results_response = await aiofiles.open(f'{folder_name}/{file_name}_{i}_results.json', 'wb')
            while part is not None:
                if part.name == 'file':
                    filedata = await part.read(decode=False)
                    await file_response.write(bytearray(filedata))
                elif part.name == 'results':
                    resultsdata = await part.read(decode=False)
                    await results_response.write(bytearray(resultsdata))
                part = await reader.next()
        queue.task_done()
        logging.info(f': Task{i} completed.')
