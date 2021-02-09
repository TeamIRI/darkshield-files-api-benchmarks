import argparse
import json
import logging
import os
import requests
import timeit
import sys

# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from setup import setup, teardown, file_mask_context_name, file_search_context_name

import utils

if __name__ == '__main__':
  logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
  parser = argparse.ArgumentParser(description='Benchmark json file search/masking.')
  parser.add_argument('file_size', type=int, help='The size of the json file in kbs.')
  parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, help='The number of times the test should be run to obtain the average. Defaults to 10.')
  
  args = parser.parse_args()
  file_size = args.file_size
  iterations = args.iterations
  test_folder = 'test-files'
  file_name = f'test-{file_size}.json'
  file_path = f'{test_folder}/{file_name}'
  os.makedirs(test_folder, exist_ok=True)
  if not os.path.exists(file_path):
    logging.info(f'Creating {file_name}...')
    with open(file_path, 'w') as f:
      open_array = f'[{os.linesep}'
      close_array = f']{os.linesep}'
      indent = '    '
      initial_size = len(open_array) + len(close_array)
      start_object = ''
      test_object = f'{indent}{{{os.linesep}{indent}{indent}"data": "This is a test"{os.linesep}{indent}}}'
      num_objects = int((file_size - initial_size) * 1000 /  len(test_object))
      f.write(open_array)
      f.write(test_object)
      for i in range(num_objects):
        f.write(f',{os.linesep}{test_object}')
      f.write(os.linesep)
      f.write(close_array)
    logging.info(f'Created {file_name}.')
  try:
    setup()
    context = json.dumps({
        "fileSearchContextName": file_search_context_name,
        "fileMaskContextName": file_mask_context_name
    })
    utils.benchmark_search_mask(file_path, context, file_size, iterations)
  finally:
    teardown()
