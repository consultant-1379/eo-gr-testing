"""Workaround for https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/EO-170463"""
from pytest import mark

# pylint: disable=unused-argument


@mark.restart_api_gateway_pod
def test_restart_api_gateway_pod(
    restart_api_gw_pod: None,
) -> None:
    """Workaround for https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/EO-170463"""
