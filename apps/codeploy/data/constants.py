"""Module with Codeploy app constants"""
from core_libs.eo.ccd.k8s_data.pods import VNFLCM_SERVICE


class CodeployDetails:
    """
    Class to store default prefixes for test data
    """

    EOCM_SECRET_NAME = "eric-eo-evnfm-nfvo"
    EOCM_CONFIG_NAME = f"{EOCM_SECRET_NAME}-config"
    DOCKER_REGISTRY_TLS_SECRET = "registry-tls-secret"
    HELM_REGISTRY_TLS_SECRET = "helm-registry-tls-secret"
    DATA_TLS_SRT = r"tls.crt"
    NAME = "name"
    DATA = "data"
    URL = "url"


class CrictlCommands:
    """
    Stores crictl commands for CRI-compatible container runtimes
    """

    GET_IMAGE_BY_PATH = "sudo crictl image list | grep {image_path}"
    REMOVE_IMAGE_BY_ID = "sudo crictl rmi {image_id}"


class HAPods:
    """
    Stores pods that support HA functionality and other HA related data
    """

    HA_PODS_LIST = [VNFLCM_SERVICE]
    NUMBER_HA_PODS = 2


class IpToolCmds:
    """
    Ip tool commands
    """

    IP_LINK_UP = "sudo ip link set {} up"
    IP_LINK_DOWN = "sudo ip link set {} down"


class NetworkInterfaces:
    """
    Stores network interfaces
    """

    ETH_0 = "eth0"
    ETH_1 = "eth1"
