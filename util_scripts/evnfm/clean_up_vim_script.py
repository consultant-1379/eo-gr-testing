"""Module to store script to clean up VIM zone from test assets"""

from argparse import ArgumentParser

from core_libs.common.constants import EnvVariables

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrEnvVariables, GR_TEST_PREFIX
from libs.common.vim_cleaner import VimCleaner
from libs.common.env_variables import ENV_VARS
from util_scripts.common.common import print_with_highlight

DESCRIPTION = f"""
Script that clean up VIM zone from test assets by asset names or by {GR_TEST_PREFIX!r} prefix\n
Required environment variables:
    - {EnvVariables.VIM}
     Optional:
    - {GrEnvVariables.GR_STAGE_SHARED_NAME}: used to find test assets that were created across the tests to remove them
Options:
    --delete-all: if provided all assets that start with {GR_TEST_PREFIX!r} prefix will be removed.
"""

if __name__ == "__main__":
    print_with_highlight(DESCRIPTION)

    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--delete-all",
        action="store_true",
    )
    delete_all = parser.parse_args().delete_all

    config = ConfigReader()
    config.read_vim(vim=ENV_VARS.vim)
    vim_cleaner = VimCleaner(config=config)

    if delete_all:
        vim_cleaner.clean_up_all_by_gr_prefix()
    else:
        vim_cleaner.clean_up_all_by_asset_names()
