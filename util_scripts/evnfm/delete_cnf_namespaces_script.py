"""Module that stores script for clean up of test cnf namespaces from cluster"""

from argparse import ArgumentParser

from libs.common.constants import GrEnvVariables, DEFAULT_NAME, GR_TEST_PREFIX
from libs.common.cvnfm_namespace_deleter import CvnfmNamespaceDeleter
from libs.common.env_variables import ENV_VARS
from libs.common.thread_runner import ThreadRunner
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config, passive_site_config

if __name__ == "__main__":
    DESCRIPTION = f"""
Delete cnf namespaces that stars with {GR_TEST_PREFIX!r} or by provided shared name from the cluster\n
Required environment variables:
    - {GrEnvVariables.ACTIVE_SITE}
    Optional:
    - {GrEnvVariables.PASSIVE_SITE}
    - {GrEnvVariables.GR_STAGE_SHARED_NAME}: if not provided {DEFAULT_NAME!r} shared name will be used
Options:
    --delete-all: if provided {GrEnvVariables.GR_STAGE_SHARED_NAME} will be ignored, all namespaces will be removed.
"""
    print_with_highlight(DESCRIPTION)

    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="If provided all CVNFM namespaces will be deleted",
    )
    delete_all = parser.parse_args().delete_all

    print_with_highlight(
        f"Start deletion namespaces from {ENV_VARS.active_site} {ENV_VARS.passive_site or ''} cluster(s)"
    )
    threads = []
    for site_config in active_site_config, passive_site_config:
        if site_config:
            ns_deleter = CvnfmNamespaceDeleter(config=site_config)
            target = (
                ns_deleter.delete_namespaces_by_default_prefix
                if delete_all
                else ns_deleter.delete_namespace_by_shared_name
            )
            thread = ThreadRunner(
                target=target,
                daemon=True,
                name=ns_deleter.cluster_name,
            )
            thread.start()
            threads.append(thread)
    for thread in threads:
        thread.join_with_result(timeout=10 * 60)

    print_with_highlight("Script finished successfully.")
