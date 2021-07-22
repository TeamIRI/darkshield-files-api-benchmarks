import argparse
import json
import logging
import os
import requests
import sys
import pandas as pd

# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from setup import setup, teardown, file_mask_context_name, file_search_context_name

import utils

# Simple setup, only fields of string type with no nesting or arrays in this benchmark.
if __name__ == '__main__':
  logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
  parser = argparse.ArgumentParser(description='Benchmark Parquet file search/masking.')
  parser.add_argument('records', type=int, help='The number of records to create for the test file.')
  parser.add_argument('fields', type=int, help='The number of fields to create for the test file.')
  parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10, help='The number of times the test should be run to obtain the average. Defaults to 10.')

  args = parser.parse_args()
  records = args.records
  fieldNumber = args.fields
  iterations = args.iterations
  test_folder = 'test-files'
  file_name = f'test-{records}.parquet'
  file_path = f'{test_folder}/{file_name}'
  os.makedirs(test_folder, exist_ok=True)
  lst = [[0] * fieldNumber for i in range(records)]
  cols = []
  for f in range(fieldNumber):
    cols.append('Test{}'.format(f))
  for r in range(records):
    for f in range(fieldNumber):
      lst[r][f] = "this is a test"
  df = pd.DataFrame(lst, columns = cols)
  df.to_parquet(file_path)
  logging.info(f'Created {file_name}.')
  with requests.Session() as session:
    try:
      setup(session)
      context = json.dumps({
          "fileSearchContextName": file_search_context_name,
          "fileMaskContextName": file_mask_context_name
      })
      utils.benchmark_search_mask(session, file_path, context, 
                                  records, 'application/x-parquet', iterations)
    finally:
      teardown(session)
