"""Script that updates kubeconfig file on JFrog artifactory and on masters"""

import yaml
from core_libs.common.console_commands import CMD
from core_libs.common.constants import (
    CcdConfigKeys,
    CommonConfigKeys,
)
from core_libs.common.jfrog_api import JfrogAPI
from core_libs.eo.ccd.constants import ClusterConfigKeys as CcKeys

from apps.codeploy.codeploy_app import CodeployApp
from apps.codeploy.master_node import MasterNode
from libs.common.constants import GrEnvVariables
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config

ECCD_KUBE_CONFIG_PATH = "/home/eccd/.kube/config"

CLUSTER_NAME = active_site_config.read_section(CommonConfigKeys.ENV_NAME)
KUBE_API_HOST = active_site_config.read_section(CcdConfigKeys.CCD_KUBE_API_HOST)
KUBE_CONF_PATH = active_site_config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH)


def get_kube_config_with_updated_host(master_node_ip: str) -> str:
    """Method to get kubeconfig from director and edit kube API host in it
    Args:
      master_node_ip: master node IP
    Raises:
      KeyError: when needed key is not found in kubeconfig
      IndexError: when there is no registered clusters in kubeconfig
      ValueError: when cluster kubeconfig is empty or does not exist
    Returns:
      kubeconfig with updated kube API host
    """
    logger.info(f"Get cluster kubeconfig from {master_node_ip=}")
    with MasterNode(active_site_config, ip=master_node_ip).set_ssh_client() as ssh:
        cluster_config = ssh.exec_cmd(CMD.CAT.format(ECCD_KUBE_CONFIG_PATH))

    if not cluster_config:
        raise ValueError("Cluster kubeconfig is empty or does not exist")

    try:
        cluster_config = yaml.safe_load(cluster_config)
        cluster_config[CcKeys.CLUSTERS][0][CcKeys.CLUSTER][
            CcKeys.SERVER
        ] = KUBE_API_HOST
        return yaml.dump(cluster_config)

    except KeyError as exc:
        raise KeyError(f"No key in kubeconfig {exc}") from None
    except IndexError as exc:
        raise IndexError(f"No registered clusters: {exc}") from None


def update_kube_config_on_master_nodes_and_on_jfrog() -> None:
    """General function for updating kubeconf on all master nodes and on Jfrog artifactory"""
    print_with_highlight("Script is running...")
    master_nodes_ips = CodeployApp(active_site_config).collect_master_nodes_ips()
    updated_kubeconfig = get_kube_config_with_updated_host(master_nodes_ips[0])

    for ip in master_nodes_ips:
        logger.info(f"Update kubeconfig on master node: {ip!r}")
        with MasterNode(active_site_config, ip=ip).set_ssh_client() as ssh:
            ssh.exec_cmd(
                CMD.ECHO_TO_FILE.format(updated_kubeconfig, ECCD_KUBE_CONFIG_PATH)
            )

    JfrogAPI(active_site_config).update_artifact_file_content(
        KUBE_CONF_PATH, updated_kubeconfig
    )
    print_with_highlight("Finished successfully!")


if __name__ == "__main__":
    print_with_highlight(
        f"""
        Script that update kubeconfig on all cluster master nodes and also update it on Jfrog artifactory.
        Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}
        """
    )
    update_kube_config_on_master_nodes_and_on_jfrog()
