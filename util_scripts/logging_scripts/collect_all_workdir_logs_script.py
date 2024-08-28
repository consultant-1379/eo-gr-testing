"""Script that collect all available logs in EO Node install workdir"""
import argparse

from libs.common.constants import GrEnvVariables
from libs.common.deployment_manager.dm_collect_logs import (
    DeploymentManagerLogCollection,
)
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config

if __name__ == "__main__":
    DESCRIPTION = f"""
    This script collects all available log files from EO Node install workdir.\n
    Additionally it may remove log/ directory when the "--clean-up" flag is set.\n
        Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}: The Environment for which needed collect logs
    """
    print_with_highlight(DESCRIPTION)

    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "--clean-up",
        action="store_true",
        help="A flag to remove all log files stored in the log/ directory on the EO Node",
    )

    args = parser.parse_args()

    dm_log_collector = DeploymentManagerLogCollection(active_site_config)

    if args.clean_up:
        dm_log_collector.delete_log_dir()
    else:
        dm_log_collector.download_all_logs()
