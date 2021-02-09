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
  parser = argparse.ArgumentParser(description='Benchmark text file search/masking.')
  parser.add_argument('lines', type=int, help='The number of text lines to create for the test file. Each line is 1kb in size.')
  parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, help='The number of times the test should be run to obtain the average. Defaults to 10.')
  parser.add_argument('-b', '--buffer-limit', metavar='N', type=int, help='Set the buffer limit to use for the text file in memory-constrained environments.')

  args = parser.parse_args()
  lines = args.lines
  iterations = args.iterations
  buffer_limit = args.buffer_limit
  test_folder = 'test-files'
  file_name = f'test-{lines}.txt'
  file_path = f'{test_folder}/{file_name}'
  os.makedirs(test_folder, exist_ok=True)
  if not os.path.exists(file_path):
    logging.info(f'Creating {file_name}...')
    test_line = 'this is a test'
    line = '#' * (1000 - len(test_line) - len(os.linesep)) + test_line + os.linesep
    with open(file_path, 'w') as f:
      for i in range(lines):
        f.write(line)
    logging.info(f'Created {file_name}.')
  try:
    setup(buffer_limit)
    context = json.dumps({
        "fileSearchContextName": file_search_context_name,
        "fileMaskContextName": file_mask_context_name
    })
    utils.benchmark_search_mask(file_path, context, lines, iterations)
  finally:
    teardown()
