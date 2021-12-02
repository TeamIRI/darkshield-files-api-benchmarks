import argparse
import json
import logging
import os
import requests
import sys

# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from setup import setup, teardown, file_mask_context_name, file_search_context_name

import utils

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='Benchmark image file search/masking.')
    parser.add_argument('-i', '--iterations', metavar='N', type=int, default=10,
                        help='The number of times the test should be run to obtain the average. Defaults to 10.')
    parser.add_argument('-f', '--file', type=str, default="example.jpeg", help='The image file to get a benchmark on.')
    args = parser.parse_args()
    iterations = args.iterations
    file_name = args.file
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"File does not exist at path {file_name}. Aborting.")
    with requests.Session() as session:
        try:
            setup(session)
            context = json.dumps({
                "fileSearchContextName": file_search_context_name,
                "fileMaskContextName": file_mask_context_name
            })
            utils.benchmark_search_mask(session, file_name, context,
                                        os.path.getsize(file_name), '', iterations)
        finally:
            teardown(session)
