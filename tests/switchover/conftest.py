"""
Is dedicated for storing the switchover-specific fixtures
"""
from typing import Generator

from pytest import fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.codeploy.pods_health_checker import PodsHealthChecker
from apps.gr.geo_redundancy import GeoRedundancyApp


@fixture(scope="session")
def healthcheck_two_sites_switchover_success(
    codeploy_app_active_site: CodeployApp,
    codeploy_app_passive_site: CodeployApp,
    is_tests_in_session_failed: callable,
) -> Generator:
    """
    Verifies switchover operation success by checking status and number of available containers
    of the dedicated pods on both sites
    Args:
        codeploy_app_active_site: CodeployApp instance of Active Site
        codeploy_app_passive_site: CodeployApp instance of Passive Site
        is_tests_in_session_failed: fixture that returns status of the test session
    """
    yield
    if is_tests_in_session_failed():
        # If test case failed we are going to make heath check for original sites
        PodsHealthChecker(
            active_site_codeploy=codeploy_app_active_site,
            passive_site_codeploy=codeploy_app_passive_site,
        ).healthcheck()
    else:
        PodsHealthChecker(
            active_site_codeploy=codeploy_app_passive_site,
            passive_site_codeploy=codeploy_app_active_site,
        ).healthcheck()


@fixture(scope="session")
def healthcheck_two_sites_switchover_rollback(
    codeploy_app_active_site: CodeployApp,
    codeploy_app_passive_site: CodeployApp,
) -> Generator:
    """
    Verifies switchover operation success by checking status and number of available containers
    of the dedicated pods on both sites after rollback operation
    Args:
        codeploy_app_active_site: CodeployApp instance of Active Site
        codeploy_app_passive_site: CodeployApp instance of Passive Site
    """
    yield
    PodsHealthChecker(
        active_site_codeploy=codeploy_app_active_site,
        passive_site_codeploy=codeploy_app_passive_site,
    ).healthcheck()


@fixture(scope="session")
def healthcheck_new_active_site(
    codeploy_app_active_site: CodeployApp,
    codeploy_app_passive_site: CodeployApp,
    is_tests_in_session_failed: callable,
) -> Generator:
    """
    Verifies switchover operation success by checking status and number of available containers
    of the dedicated pods on new active site
    Args:
        codeploy_app_active_site: CodeployApp instance of Active Site
        codeploy_app_passive_site: CodeployApp instance of Passive Site
        is_tests_in_session_failed: fixture that returns status of the test session
    """
    yield
    if is_tests_in_session_failed():
        # If test case failed we are going to make heath check for original sites
        PodsHealthChecker(active_site_codeploy=codeploy_app_active_site).healthcheck()
    else:
        PodsHealthChecker(active_site_codeploy=codeploy_app_passive_site).healthcheck()


@fixture(scope="session")
def decrease_backup_cycle_interval_and_check_new_backup_created(
    decrease_backup_cycle_interval_on_both_sites: None,  # pylint: disable=unused-argument
    gr_app: GeoRedundancyApp,
) -> bool:
    """
    Fixture to use in switchover with backup ID  from availability cmd test
    in order to prevent making switchover with backup which does not contain the most recent data
    Args:
        decrease_backup_cycle_interval_on_both_sites: change default interval value for creating backup on both sites
        gr_app: GeoRedundancyApp instance
    Returns:
        True if backup is updated in availability cmd to the new one, else raises exception

    """
    return gr_app.verify_backup_id_updated_in_availability(interval=10.0)
