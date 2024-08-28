"""This module contains tests related to Geographical Redundancy Switchover functionality"""
import asyncio
from typing import Generator

from pytest import mark

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.geo_redundancy import GeoRedundancyApp

# pylint: disable=unused-argument


@mark.switchover_rollback_bur_pod
def test_switchover_rollback_after_bur_pod_restarting(
    gr_app: GeoRedundancyApp,
    make_switchover_and_kill_pod: callable,
    codeploy_app_passive_site: CodeployApp,
    healthcheck_two_sites_switchover_rollback: Generator,
):
    """
    Make Geographical Redundancy Rollback when bur-orchestrator pod restarted
    Args:
        gr_app: GeoRedundancyApp instance
        make_switchover_and_kill_pod: fixture that makes switchover and kills a pod
        codeploy_app_passive_site: CodeployApp instance with passive site config
        healthcheck_two_sites_switchover_rollback: verifies that pods are in expected states after switchover done
    """
    is_gr_availability = gr_app.verify_gr_availability()
    assert (
        is_gr_availability
    ), "EO GR hasn't become available after the switchover operation"

    is_geo_status_success = gr_app.gr_status.make_and_verify_geo_status_command()
    assert (
        is_geo_status_success
    ), "GR Status command contains missmatch for performing switchover"

    asyncio.run(
        make_switchover_and_kill_pod(
            codeploy_app_passive_site.restart_bur_pod_when_gr_pods_ready_async
        )
    )
