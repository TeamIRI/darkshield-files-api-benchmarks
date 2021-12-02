import utils
import pathlib

search_context_name = "SearchContext"
mask_context_name = "MaskContext"
file_search_context_name = "FileSearchContext"
file_mask_context_name = "FileMaskContext"


def setup(session):
    search_context = {
        "name": search_context_name,
        "matchers": [
            {
                "name": "SsnMatcher",
                "type": "pattern",
                "pattern": r"\b(\d{3}[-]?\d{2}[-]?\d{4})\b"
            },
            {
                "name": "NameMatcher",
                "type": "set",
                "url": pathlib.Path('names.set').absolute().as_uri()
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
                "pattern": ".*"
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
