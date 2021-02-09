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
  parser = argparse.ArgumentParser(description='Benchmark xml file search/masking.')
  parser.add_argument('file_size', type=int, help='The size of the xml file in kbs.')
  parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, help='The number of times the test should be run to obtain the average. Defaults to 10.')
  
  args = parser.parse_args()
  file_size = args.file_size
  iterations = args.iterations
  test_folder = 'test-files'
  file_name = f'test-{file_size}.xml'
  file_path = f'{test_folder}/{file_name}'
  os.makedirs(test_folder, exist_ok=True)
  if not os.path.exists(file_path):
    logging.info(f'Creating {file_name}...')
    with open(file_path, 'w') as f:
      header = f'<?xml version="1.0" encoding="UTF-8"?>{os.linesep}'
      open_tag = f'<div>{os.linesep}'
      close_tag = f'</div>{os.linesep}'
      test_line = f'    <div>This is a test</div>{os.linesep}'
      initial_size = len(header) + len(open_tag) + len(close_tag)
      num_tags = int((file_size - initial_size) * 1000 / len(test_line))
      f.write(header)
      f.write(open_tag)
      for i in range(num_tags):
        f.write(test_line)
      f.write(close_tag)
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
