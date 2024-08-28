"""This module contains tests related to Geographical Redundancy Switchover functionality"""
import asyncio
from typing import Generator

from pytest import mark

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.geo_redundancy import GeoRedundancyApp

# pylint: disable=unused-argument


@mark.switchover_rollback_bro_pod
def test_switchover_rollback_after_bro_pod_restarting(
    gr_app: GeoRedundancyApp,
    codeploy_app_passive_site: CodeployApp,
    make_switchover_and_kill_pod: callable,
    healthcheck_two_sites_switchover_rollback: Generator,
):
    """
    Make Geographical Redundancy Rollback when eric-ctrl-bro pod restarted
    Args:
        gr_app: GeoRedundancyApp instance
        make_switchover_and_kill_pod: fixture that makes switchover and kills a pod
        codeploy_app_passive_site: CodeployApp instance with passive site config
        healthcheck_two_sites_switchover_rollback: verifies that pods are in expected states after switchover done
    """
    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"

    assert (
        gr_app.gr_status.make_and_verify_geo_status_command()
    ), "GR Status command contains missmatch for performing switchover"

    asyncio.run(
        make_switchover_and_kill_pod(
            codeploy_app_passive_site.restart_bro_pod_when_db_pod_starts_to_recreate_async
        )
    )
