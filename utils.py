import logging
import numpy as np
import os
import pathlib
import timeit

from requests_toolbelt import MultipartEncoder
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget

host = 'http://localhost:8080/api/darkshield'

def create_context(session, context, data):
  url = f'{host}/{context}.create'
  logging.info(f'POST: {url}')
  with session.post(url, json=data) as r:
    if r.status_code >= 300:
      raise Exception(f"Failed with status {r.status_code}:\n\n{r.json()}")


def destroy_context(session, context, name):
  url = f'{host}/{context}.destroy'
  logging.info(f'POST: {url}')
  session.post(url, json={'name': name})


def benchmark_search_mask(session, file_path, context, file_size, media_type, iterations, chunk_size=4096):
  folder_name = f'results/{file_size}'
  def send():  
    url = f'{host}/files/fileSearchContext.mask'
    headers = {'Accept-Encoding': "gzip", 'Transfer-Encoding': "gzip"}
    extension = os.path.splitext(file_path)[1]
    os.makedirs(folder_name, exist_ok=True)
    with open(file_path, 'rb') as f:
      encoder = MultipartEncoder(fields={
        'context': ('context', context, 'application/json'),
        'file': ('file', f, media_type)
      })
      with session.post(url, data=encoder, stream=True,
                        headers={'Content-Type': encoder.content_type}) as r:
        if r.status_code >= 300:
          raise Exception(f"Failed with status {r.status_code}:\n\n{r.json()}")

        parser = StreamingFormDataParser(headers=r.headers)
        parser.register('file', FileTarget(f'{folder_name}/masked{extension}'))
        parser.register('results', FileTarget(f'{folder_name}/results.json'))
        for chunk in r.iter_content(chunk_size):
          parser.data_received(chunk)

  times = timeit.repeat(send, number=1, repeat=iterations)
  results_file = f'{folder_name}/benchmarks.txt'
  with open(results_file, 'w') as f:
    f.write(f'Iterations: {iterations}{os.linesep}')
    f.write(f'Lowest: {np.min(times)} seconds{os.linesep}')
    f.write(f'Highest: {np.max(times)} seconds{os.linesep}')
    f.write(f'Mean: {np.mean(times)} seconds{os.linesep}')
    f.write(f'Median: {np.median(times)} seconds{os.linesep}')
    f.write(f'Stdev: {np.std(times)} seconds{os.linesep}')
    f.write(f'Variance: {np.var(times)} seconds{os.linesep}')
  logging.info(f'Written out {results_file}.')
