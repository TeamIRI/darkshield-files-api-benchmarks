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
  parser = argparse.ArgumentParser(description='Benchmark csv file search/masking.')
  parser.add_argument('lines', type=int, help='The number of csv lines to create for the test file. Each line is 1kb in size.')
  parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, help='The number of times the test should be run to obtain the average. Defaults to 10.')
  
  args = parser.parse_args()
  lines = args.lines
  iterations = args.iterations
  test_folder = 'test-files'
  file_name = f'test-{lines}.csv'
  file_path = f'{test_folder}/{file_name}'
  os.makedirs(test_folder, exist_ok=True)
  if not os.path.exists(file_path):
    logging.info(f'Creating {file_name}...')
    with open(file_path, 'w') as f:
      test = 'this is a test'
      char_num = 1000 - len(test) - len(os.linesep)
      chars_per_col = 10
      num_cols = int(char_num / chars_per_col)
      remaining_padding = 'x' * (char_num % chars_per_col)
      line = ','.join(['x' * (chars_per_col - 1) for i in range(num_cols)] + [f'{remaining_padding}this is a test'])
      for i in range(lines):
        f.write(line)
        f.write(os.linesep)
    logging.info(f'Created {file_name}.')
  with requests.Session() as session:
    try:
      setup(session)
      context = json.dumps({
          "fileSearchContextName": file_search_context_name,
          "fileMaskContextName": file_mask_context_name
      })
      utils.benchmark_search_mask(session, file_path, context, lines, iterations)
    finally:
      teardown(session)
