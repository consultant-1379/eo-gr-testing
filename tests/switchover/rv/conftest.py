"""Module to store RV switchover related fixtures"""

import asyncio

from pytest import fixture

from apps.gr.data.constants import GrSearchPatterns
from apps.gr.geo_redundancy import GeoRedundancyApp
from libs.utils.common_utils import is_pattern_match_text


@fixture
def make_switchover_and_kill_pod(gr_app: GeoRedundancyApp) -> callable:
    """
    Fixture that in parallel runs switchover and waits for specific condition for killing provided pod
    Args:
        gr_app: GeoRedundancyApp instance
    Returns:
        callable function
    """

    async def inner_func(restart_pod_func: callable) -> None:
        """
        Make switchover and wait for condition to killing the pod
        Args:
            restart_pod_func: function to restart desired pod while switchover running
        """
        switchover_task_name = "switchover"

        async with asyncio.TaskGroup() as tg:
            tg.create_task(restart_pod_func(switchover_task_name))

            task_switchover = tg.create_task(
                gr_app.make_switchover_async(), name=switchover_task_name
            )
        switchover_output = task_switchover.result()

        assert is_pattern_match_text(
            GrSearchPatterns.SWITCH_OVER_FAILURE_STATUS, switchover_output, group=0
        ), "Switchover rollback operation finned with unexpected status"
        assert is_pattern_match_text(
            GrSearchPatterns.SWITCH_OVER_NO_HEALTHY_UPSTREAM,
            switchover_output,
            group=0,
        ), "Wrong switchover rollback operation error text"

    return inner_func
