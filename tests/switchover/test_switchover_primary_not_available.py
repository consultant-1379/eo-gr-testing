"""This module contains tests related to Geographical Redundancy Switchover functionality"""
from typing import Generator

from core_libs.eo.ccd.k8s_data.pods import ERIC_GR_BUR_ORCH
from pytest import mark

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.geo_redundancy import GeoRedundancyApp


# pylint: disable=unused-argument


@mark.switchover_active_site_not_available
def test_make_geo_redundancy_primary_site_not_available(
    decrease_backup_cycle_interval_and_check_new_backup_created: None,
    gr_app: GeoRedundancyApp,
    codeploy_app_active_site: CodeployApp,
    healthcheck_new_active_site: Generator,
) -> None:
    """
    Make Geographical Redundancy by the next steps:
    - check availability
    - check geo status
    - change replicas to 0 for pod gr-but
    - check availability
    - check geo status when primary site is down
    - make switchover

    Args:
        decrease_backup_cycle_interval_and_check_new_backup_created: decrease backup interval and
                                                                    check new backup created
        gr_app: GeoRedundancyApp instance
        codeploy_app_active_site: CodeployApp instance with active site config
        healthcheck_new_active_site: verifies that pods are in expected states after switchover done
    """
    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"

    assert (
        gr_app.gr_status.make_and_verify_geo_status_command()
    ), "GR Status command contains missmatch for performing switchover"

    codeploy_app_active_site.change_deployment_replicas(ERIC_GR_BUR_ORCH, replicas=0)

    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"

    assert (
        gr_app.gr_status.geo_status_if_primary_not_alive()
    ), "GR Status command contains missmatch for performing switchover"

    backup_id = gr_app.get_backup_id_from_availability()
    is_switchover_success = gr_app.make_and_verify_switchover(backup_id=backup_id)
    assert is_switchover_success, "Switchover completed with errors"
