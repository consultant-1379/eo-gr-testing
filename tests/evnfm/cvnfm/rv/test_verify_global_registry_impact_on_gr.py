"""Test that verifies the global registry availability impact on the EO GR"""
import re

from core_libs.common.constants import K8sKeys
from core_libs.eo.ccd.k8s_data.pod_model import K8sPod
from core_libs.eo.ccd.k8s_data.pods import ERIC_GR_BUR_ORCH
from core_libs.eo.constants import ApiKeys
from pytest import mark, fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.codeploy.data.constants import CrictlCommands
from libs.common.asset_names import AssetNames
from libs.utils.logging.logger import logger, log_exception

# pylint: disable=unused-argument

pytestmark = [mark.global_registry_impact_on_gr]


@fixture(scope="function")
def override_dns_config(codeploy_app_passive_site: CodeployApp) -> list:
    """
    Generates data for overriding the default DNS server configurations
    Args:
        codeploy_app_passive_site: a CodeployApp object for Passive Site
    Returns:
        A list of strings in a form of '<ICCR_IP>:<host_address>'
        to be overriden in the default DNS server configuration
    """
    logger.info(
        "Preparing a list of ICCR_IP and hosts to override the default DNS configuration "
    )

    logger.info(
        f"A pair {codeploy_app_passive_site.iccr_ip}:{codeploy_app_passive_site.global_registry_host} "
        f"will be added to the DNS config"
    )
    return [
        f"{codeploy_app_passive_site.iccr_ip}:{codeploy_app_passive_site.global_registry_host}"
    ]


@fixture(scope="function")
def remove_image_from_worker_node(
    codeploy_app_active_site: CodeployApp, asset_names: AssetNames
) -> callable:
    """
    Removes an image from a worker node of the dedicated pod deployed from the CNF package
    Args:
        codeploy_app_active_site: a CodeployApp instance
        asset_names: an AssetNames instance with CNF instance name based on given value of environment variable
    Returns:
        A function that performs all described steps
    """

    def inner_func(pod: K8sPod) -> bool:
        """
        A function that removes instance image from a worker node of the dedicated pod
        deployed from the CNF package.
        Please note: it is specific for spider-app-multi-a-etsi-tosca-rel4-option1-and-option2-1.0.43.zip
        and highly likely won't work with instances deployed from other packages!
        Args:
            pod: K8sPod instance
        Returns:
            True if the image has been successfully removed, otherwise - False
        """
        logger.info(f"Getting detailed info of {pod.name}")

        pod_data = codeploy_app_active_site.k8s_eo_client.get_pod(
            pod=pod, namespace=asset_names.cnf_instance_name
        ).to_dict()
        worker_node_ip = pod_data[ApiKeys.STATUS][K8sKeys.HOST_IP]
        image_path = pod_data[K8sKeys.SPEC][K8sKeys.CONTAINERS][0][K8sKeys.IMAGE].split(
            ":"
        )[0]
        logger.info(
            f"Removing image {image_path} from the worker node {worker_node_ip}"
        )
        with codeploy_app_active_site.connect_master_node(
            worker_ip=worker_node_ip,
            worker_username=codeploy_app_active_site.master_node.username,
        ) as master_node_ssh:
            out = master_node_ssh.exec_cmd(
                CrictlCommands.GET_IMAGE_BY_PATH.format(image_path=image_path),
                on_worker=True,
            )
            image_name = image_path.split("/").pop()
            reg_exp = image_name + r"\s+\d+\.\d+\.\d+\s+(?P<image_id>\w+)"
            result = re.search(reg_exp, out)
            image_id = result.groupdict().get("image_id")
            rm_image_output = master_node_ssh.exec_cmd(
                CrictlCommands.REMOVE_IMAGE_BY_ID.format(image_id=image_id),
                on_worker=True,
            )
            return f"Deleted: {image_path}" in rm_image_output

    return inner_func


def test_global_registry_impact_on_gr(
    instantiate_cnf_package_and_clean_up,
    codeploy_app_active_site,
    asset_names: AssetNames,
    deploy_dns_server,
    override_dns_config,
    remove_image_from_worker_node,
) -> None:
    """
    Prerequisites:
        This test requires the customer-like EO installation on both sites
    Test steps:
        1. Instantiate CNF on site A
        2. Find a docker image name and version of any pod created by the instantiated CNF
        3. Scale eric-gr-bur-orchestrator replicaset to 0 on the active site
        4. Run DNS (dnsmasq) server with config file, where all hostnames of the active site are mapped to site its IP,
           except the global registry hostname which is mapped ONLY to the passive site's IP
        5. Cleanup instantiated CNF docker images (cleanup cache) on CISM cluster:
           go to the worker node where the pod is running and remove its docker image
        6. Verify that CNF pod is recreated, as its docker images were taken from global registry,
            despite it has only site B ip address
        7. On site A scale eo-gr-orchestrator replica set to the original value
        8. Clean up the DNS server configuration
        9. Terminate CNF and remove onboarded CNF package
    """
    zero = 0
    one = 1
    cnf_instance_name = asset_names.cnf_instance_name
    cnf_instance_pm_testapp = K8sPod(
        name=f"{cnf_instance_name}-2-pm-testapp",
        container="pm-testapp",
    )
    try:
        logger.info(f"Scaling replicaset {ERIC_GR_BUR_ORCH.name} to {zero}")
        codeploy_app_active_site.change_deployment_replicas(
            pod=ERIC_GR_BUR_ORCH, replicas=zero
        )

        deploy_dns_server(override=override_dns_config)

        assert remove_image_from_worker_node(cnf_instance_pm_testapp), log_exception(
            f"Failed to remove the image from worker node of the {cnf_instance_pm_testapp.name} pod"
        )

        logger.info(
            f"Restarting {cnf_instance_pm_testapp.name} pod and waiting until it's up"
        )
        codeploy_app_active_site.k8s_eo_client.delete_pod(
            pod=cnf_instance_pm_testapp, namespace=cnf_instance_name
        )
        codeploy_app_active_site.k8s_eo_client.wait_till_pod_recreated_and_up(
            cnf_instance_pm_testapp, namespace=cnf_instance_name
        )

    finally:
        logger.info(f"Scaling replicaset {ERIC_GR_BUR_ORCH.name} to {one}")
        codeploy_app_active_site.change_deployment_replicas(
            pod=ERIC_GR_BUR_ORCH, replicas=one
        )
