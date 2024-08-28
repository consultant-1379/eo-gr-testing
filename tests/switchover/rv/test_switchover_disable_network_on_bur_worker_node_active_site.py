"""This module contains tests related to Geographical Redundancy Switchover functionality"""

from core_libs.eo.ccd.constants import NodeStatus
from core_libs.eo.ccd.k8s_data.pods import ERIC_GR_BUR_ORCH, COMMON_WFS
from pytest import fixture, mark

from apps.codeploy.codeploy_app import CodeployApp
from apps.codeploy.data.constants import IpToolCmds, NetworkInterfaces as Interfaces
from apps.gr.data.constants import GrTimeouts
from apps.gr.geo_redundancy import GeoRedundancyApp
from libs.utils.common_utils import join_cmds
from libs.utils.logging.logger import logger


@fixture
def disable_network_interfaces_on_worker_where_bur_pod_active_site_runs(
    codeploy_app_active_site: CodeployApp,
) -> callable:
    """Disable network interfaces on a worker node where bur pod of active site runs
    Args:
        codeploy_app_active_site: CodeployApp instance of active site
    Returns:
        function to disable the network interfaces inside node
    """
    disable_and_enable_networks_cmd = join_cmds(
        [
            IpToolCmds.IP_LINK_DOWN.format(Interfaces.ETH_1),
            IpToolCmds.IP_LINK_DOWN.format(Interfaces.ETH_0),
            "sleep 420",
            IpToolCmds.IP_LINK_UP.format(Interfaces.ETH_1),
            IpToolCmds.IP_LINK_UP.format(Interfaces.ETH_0),
        ]
    )

    def disable_network_interfaces_inner_func() -> None:
        """Inner function"""
        bur_pod_name_active_site = (
            codeploy_app_active_site.k8s_eo_client.get_pod_full_name(
                pod=ERIC_GR_BUR_ORCH
            )
        )
        pod_details = codeploy_app_active_site.k8s_eo_client.get_pod(
            pod_full_name=bur_pod_name_active_site
        )
        worker_node_ip = pod_details.status.host_ip
        worker = pod_details.spec.node_name

        logger.info(
            f"Disabling network interfaces ({Interfaces.ETH_0!r} and {Interfaces.ETH_1!r}) on {worker=} "
            f"with {worker_node_ip=} by executing cmd: {disable_and_enable_networks_cmd!r}"
        )

        with codeploy_app_active_site.connect_master_node(
            worker_ip=worker_node_ip,
            worker_username=codeploy_app_active_site.master_node.username,
        ) as master_node_ssh:
            try:
                master_node_ssh.exec_cmd(
                    cmd=disable_and_enable_networks_cmd,
                    on_worker=True,
                    timeout=5,
                )
            # In case with disabling networking inside a Node we expect to lose SSH connectivity with it
            except TimeoutError:
                logger.debug(f"Network interfaces for {worker=} has been disabled")
            else:
                raise RuntimeError(
                    f"Network interfaces for {worker=} has NOT been disabled!"
                )
        codeploy_app_active_site.k8s_eo_client.wait_for_node_status(
            name=worker, status=NodeStatus.NOT_READY
        )
        codeploy_app_active_site.k8s_eo_client.is_new_pod_up_and_running(
            old_pod_full_name=bur_pod_name_active_site, pod=ERIC_GR_BUR_ORCH
        )

    return disable_network_interfaces_inner_func


@mark.switchover_disable_network_on_bur_worker_node_active_site
def test_switchover_disable_network_on_bur_worker_node_active_site(
    gr_app: GeoRedundancyApp,
    codeploy_app_passive_site: CodeployApp,
    disable_network_interfaces_on_worker_where_bur_pod_active_site_runs: callable,
    healthcheck_new_active_site: None,  # pylint: disable=unused-argument
):
    """
    This test performs and verifies the following:
        1. Make geo availability
        2. Make geo status
        3. Run switchover w/o backup ID
        4. Check when eric-am-common-wfs pod is up on Passive Site while switchover runs
        5. Disable network interfaces on worker node where BUR pod of Active Site runs
        6. Verify switchover finished w/o errors

    test ids: ТС7, OTC-14062
    """
    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"

    assert (
        gr_app.gr_status.make_and_verify_geo_status_command()
    ), "GR Status command contains missmatch for performing switchover"

    switchover_thread = gr_app.make_and_verify_switchover_in_separate_thread()

    logger.info(
        f"Wait until {COMMON_WFS.name} pod is not up on Passive Site while switchover running..."
    )
    switchover_thread.wait_for_condition_while_thread_is_alive(
        lambda: codeploy_app_passive_site.k8s_eo_client.is_pod_exists(pod=COMMON_WFS)
    )
    disable_network_interfaces_on_worker_where_bur_pod_active_site_runs()

    assert switchover_thread.join_with_result(
        timeout=GrTimeouts.SWITCHOVER_TIMEOUT
    ), "Switchover finished with errors. Check logs for more details."
