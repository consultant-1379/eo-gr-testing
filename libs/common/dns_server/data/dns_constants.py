"""Stores DNS related data"""

from pathlib import Path

from core_libs.eo.ccd.k8s_data.pod_model import K8sPod


class DnsServerPaths:
    """Stores DNS related paths"""

    DNS_CONFIGMAP = Path("resources/dns-deployment-data/dns-server-configmap.yaml")
    DNS_DEPLOYMENT = Path("resources/dns-deployment-data/dns-server-deployment.yaml")
    DNS_SERVICE = Path("resources/dns-deployment-data/dns-server-service.yaml")


class DnsFileConstants:
    """Stores related to DNS configuration file names"""

    RESOLV_CONF = "resolv.conf"
    DNSMASQ_CONF = "dnsmasq.conf"
    DOCKER_CONF_JSON = "dockerconfigjson"


class DnsServerK8sConstants:
    """Stores K8s DNS server related data"""

    DEPLOYMENT_NAME = "dnsmasq-server-deployment"
    CONTAINER_NAME = "dnsmasq-server"
    SERVICE_NAME = "dnsmasq-server-service"


DSN_SERVER_POD = K8sPod(
    name=DnsServerK8sConstants.DEPLOYMENT_NAME,
    container=DnsServerK8sConstants.CONTAINER_NAME,
)
