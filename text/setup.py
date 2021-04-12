import os
import utils

search_context_name = "SearchContext"
mask_context_name = "MaskContext"
file_search_context_name = "FileSearchContext"
file_mask_context_name = "FileMaskContext"

def setup(session, buffer_limit):   
  search_context = {
    "name": search_context_name,
    "matchers": [
      {
        "name": "TestMatcher",
        "type": "pattern",
        "pattern": "test"
      }
    ]
  }

  mask_context = {
    "name": mask_context_name,
    "rules": [
      {
        "name": "TestRule",
        "type": "cosort",
        "expression": "enc_fp_aes256_alphanum($\{NAME\})"
      }
    ],
    "ruleMatchers": [
      {
        "name": "TestNameRuleMatcher",
        "type": "name",
        "rule": "TestRule",
        "pattern": "TestMatcher"
      }
    ]
  }

  file_search_context = {
    "name": file_search_context_name,
    "matchers": [
      {
        "name": search_context_name,
        "type": "searchContext"
      }
    ]
  }
  if buffer_limit is not None:
    file_search_context['configs'] = {
      'text': {
        'bufferLimit': buffer_limit,
        'delimiter': os.linesep
      }
    }

  file_mask_context = {
    "name": file_mask_context_name,
    "rules": [
      {
        "name": mask_context_name,
        "type": "maskContext"
      }
    ]
  }

  utils.create_context(session, "searchContext", search_context)
  utils.create_context(session, "maskContext", mask_context)
  utils.create_context(session, "files/fileSearchContext", file_search_context)
  utils.create_context(session, "files/fileMaskContext", file_mask_context)


def teardown(session):
  utils.destroy_context(session, "searchContext", search_context_name)
  utils.destroy_context(session, "maskContext", mask_context_name)
  utils.destroy_context(session, "files/fileSearchContext", file_search_context_name)
  utils.destroy_context(session, "files/fileMaskContext", file_mask_context_name)
