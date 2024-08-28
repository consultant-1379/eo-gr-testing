"""This module contains tests related to Geographical Redundancy Switchover functionality"""

from typing import Generator

from core_libs.eo.ccd.k8s_data.pods import ERIC_GR_BUR_ORCH
from pytest import mark

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.geo_redundancy import GeoRedundancyApp


# pylint: disable=unused-argument

pytestmark = [mark.make_passive_site_available_and_run_switchover]


@mark.make_passive_site_available
def test_make_passive_site_available(codeploy_app_passive_site: CodeployApp):
    """
    Make Geographical Redundancy

    Args:
        codeploy_app_passive_site: CodeployApp instance for standby site
    """
    codeploy_app_passive_site.change_deployment_replicas(ERIC_GR_BUR_ORCH, replicas=1)


@mark.switchover
def test_make_geo_redundancy(
    gr_app: GeoRedundancyApp,
    healthcheck_two_sites_switchover_success: Generator,
) -> None:
    """
    Make Geographical Redundancy

    Args:
        gr_app: GeoRedundancyApp instance
        healthcheck_two_sites_switchover_success: verifies that pods are in expected states after switchover done
    """
    is_gr_availability = gr_app.verify_gr_availability()
    assert (
        is_gr_availability
    ), "EO GR hasn't become available after the switchover operation"

    is_geo_status_success = gr_app.gr_status.make_and_verify_geo_status_command()
    assert (
        is_geo_status_success
    ), "GR Status command contains missmatch for performing switchover"

    is_switchover_success = gr_app.make_and_verify_switchover()
    assert is_switchover_success, "Switchover completed with errors"
