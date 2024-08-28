"""Module that stores functions related to pre/post switchover steps"""


from argparse import ArgumentParser
from libs.common.constants import GrEnvVariables
from libs.common.deployment_manager.dm_collect_logs import (
    DeploymentManagerLogCollection,
)
from util_scripts.common.common import print_with_highlight, verify_passive_site_env_var
from util_scripts.common.config_reader import original_primary_site


def main(is_pre_install: bool, is_post_install: bool) -> None:
    """Run job actions depends on provided parameters

    Args:
        is_pre_install: true if pre_install step need to be executed
        is_post_install: true if post_install step need to be executed
    """
    dm_log_collector = DeploymentManagerLogCollection(original_primary_site)
    if is_pre_install:
        dm_log_collector.delete_log_dir()
    if is_post_install:
        dm_log_collector.download_all_logs()


if __name__ == "__main__":
    DESCRIPTION = f"""
    The following script:
    deletes log folder from workdir as pre-build step and download logs files as post-install step\n
    Required environment variables:\n
        - {GrEnvVariables.ACTIVE_SITE}
        - {GrEnvVariables.PASSIVE_SITE}

    Expected at least one of arguments to be provided:
        --pre-install
        --post-install
    """
    print_with_highlight(DESCRIPTION)
    verify_passive_site_env_var()

    parser = ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "--pre-install",
        action="store_true",
        help="Mark it true if it pre-install step. It will delete log folder from workdir",
    )
    parser.add_argument(
        "--post-install",
        action="store_true",
        help="Mark it true if it post-install step. It will download logs from workdir",
    )

    args = parser.parse_args()
    main(args.pre_install, args.post_install)
    print_with_highlight("Script successfully finished!")
