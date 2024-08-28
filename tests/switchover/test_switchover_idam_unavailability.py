"""
This module contains tests related to Geographical Redundancy Switchover functionality:
Verify idam unavailability impact on EO GR switchover
"""

from datetime import datetime, timezone

from pytest import mark, fixture

from core_libs.eo.ccd.k8s_data.pods import IDAM_DB_PG

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.data.constants import GrTimeouts
from apps.gr.geo_redundancy import GeoRedundancyApp

from libs.common.thread_runner import ThreadRunner
from libs.utils.logging.logger import logger


@fixture
def get_idam_db_leader_name_after_pods_recreation(
    codeploy_app_passive_site: CodeployApp,
) -> callable:
    """
    Fixture that checks for idam's db pods recreation during switchover run and then return new leader pod name
    Args:
        codeploy_app_passive_site: CodeployApp passive site instance
    Returns:
        function that checks for idam's db pods recreation during switchover run and then return new leader pod name
    """

    def inner(switchover_thread: ThreadRunner) -> str:
        """
        Checks for idam's db pods recreation during switchover run and then return new leader pod name
        Args:
            switchover_thread: thread instance with switchover run
        Returns:
            leader pod name
        """
        k8s_passive_site = codeploy_app_passive_site.k8s_eo_client
        # use current datetime in UTC timezone to checking recreation of stateful set idam's pods
        comparison_datetime = datetime.now(tz=timezone.utc)

        k8s_passive_site.wait_till_all_replicas_up(pod=IDAM_DB_PG)
        pod_names = k8s_passive_site.get_pods_full_names(pod=IDAM_DB_PG)

        switchover_thread.wait_for_condition_while_thread_is_alive(
            lambda: k8s_passive_site.is_stateful_set_pods_recreated(
                pod_names=pod_names, comparison_datetime=comparison_datetime
            )
        )
        return codeploy_app_passive_site.get_idam_db_pod_leader_name()

    return inner


@mark.switchover_idam_unavailability
def test_switchover_idam_db_leader_pod_unavailability(
    gr_app: GeoRedundancyApp,
    codeploy_app_passive_site: CodeployApp,
    get_idam_db_leader_name_after_pods_recreation: callable,
    healthcheck_two_sites_switchover_success,  # pylint: disable=unused-argument
) -> None:
    """
    Verify idam unavailability impact on EO GR switchover.

    This test performs and verifies the following:
        1. Make geo availability.
        2. Make geo status.
        3. Run switchover w/o backup ID.
        4. Wait for idam database pods recreation on Passive (new Active) Site.
        5. Delete idam db pod leader -> Check leader switches to another idam db pod.
        6. Verify there is no impact on switchover, and it finished successfully.

    JIRA: OTC-14221
    """
    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"

    assert (
        gr_app.gr_status.make_and_verify_geo_status_command()
    ), "GR Status command contains missmatch for performing switchover"

    switchover_thread = gr_app.make_and_verify_switchover_in_separate_thread()

    db_leader = get_idam_db_leader_name_after_pods_recreation(switchover_thread)

    # delete idam's leader
    codeploy_app_passive_site.k8s_eo_client.delete_pod(pod_full_name=db_leader)

    logger.info("Check leader switches to another idam db pod.")
    switchover_thread.wait_for_condition_while_thread_is_alive(
        lambda: db_leader != codeploy_app_passive_site.get_idam_db_pod_leader_name(),
        interval=1,
    )
    logger.info("Waiting for the switchover to end...")

    assert switchover_thread.join_with_result(
        timeout=GrTimeouts.SWITCHOVER_TIMEOUT
    ), "Switchover finished with errors. Check logs for more details."
