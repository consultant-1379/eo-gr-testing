"""This module contains tests related to Geographical Redundancy Switchover functionality"""
from pytest import mark, fixture
from pytest_check import check


from core_libs.common.console_commands import CMD
from core_libs.eo.ccd.k8s_data.pods import ERIC_CTRL_BRO
from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.data.constants import GrSearchPatterns
from apps.gr.geo_redundancy import GeoRedundancyApp
from libs.utils.logging.logger import logger
from libs.utils.common_utils import is_pattern_match_text

# pylint: disable=unused-argument

BRO_FILESYSTEM = "/bro"
LARGE_FILE_PATH = f"{BRO_FILESYSTEM}/large_file.txt"


@fixture
def remove_large_file_on_teardown(codeploy_app_active_site: CodeployApp) -> None:
    """
    Removes the large file generated in the test
    Args:
        codeploy_app_active_site: CodeployApp object of the active site
    """
    yield
    logger.info(f"Removing {LARGE_FILE_PATH}...")
    codeploy_app_active_site.k8s_eo_client.exec_in_pod(
        pod=ERIC_CTRL_BRO, cmd=CMD.RM.format(LARGE_FILE_PATH)
    )


@mark.switchover_no_free_space_on_bro_pod
def test_switchover_no_free_space_on_bro_pod(
    gr_app: GeoRedundancyApp,
    codeploy_app_active_site: CodeployApp,
    remove_large_file_on_teardown: None,
):
    """
    Attempt to make a switchover when there is no free space on the bro pod available
    Test steps:
        1. Check available free space on ctrl-bro pod via kubectl -n eo-deploy exec -it eric-ctrl-bro-0 – sh -> df -h.
        This check gives understanding what size of a large file should be emulated in the next step
        2. Emulate no free space on eric-ctrl-bro PVC on PRIMARY site via command
        'head -c <free space size form previous step>G /dev/zero > largefile.txt'
        3. Check available free space on ctrl-bro pod via kubectl -n eo-deploy exec -it eric-ctrl-bro-0 – sh -> df -h.
        Expected no free space
        4. Trigger switchover from PRIMARY site to SECONDARY
        5. Expected result: http 500 Internal server error with the message "Error handling persisted file"
            Note: no switchback is tested here to save time
    Args:
        gr_app: GeoRedundancyApp instance
        codeploy_app_active_site: CodeployApp instance of the active site
        remove_large_file_on_teardown: fixture that removes a file created in the test from the BRO pod
    """
    codeploy_app_active_site.fill_up_free_memory_on_pod(
        ERIC_CTRL_BRO, BRO_FILESYSTEM, LARGE_FILE_PATH
    )
    logger.info("Attempting to make a switchover...")
    switchover_stdout = gr_app.make_switchover()
    with check:
        switchover_failure = is_pattern_match_text(
            GrSearchPatterns.SWITCH_OVER_FAILURE_STATUS, switchover_stdout, group=0
        )
        assert (
            switchover_failure
        ), "The switchover status is not 'Failure' as it was expected"
    with check:
        internal_error = is_pattern_match_text(
            GrSearchPatterns.SWITCHOVER_NO_FREE_MEMORY, switchover_stdout, group=0
        )
        assert (
            internal_error
        ), "No 'Error handling persisted file' message in the switchover output"
