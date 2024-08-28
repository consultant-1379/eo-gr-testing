"""Module with BaseDns class"""

from functools import cached_property

from core_libs.common.constants import CommonConfigKeys, CcdConfigKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    GrConfigKeys,
    DEFAULT_DOWNLOAD_LOCATION,
)
from libs.common.dns_server.data.dns_constants import DnsServerK8sConstants
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class BaseDns:
    """Base class for DNS server"""

    def __init__(self, active_site_config: ConfigReader):
        self.active_site_config = active_site_config
        self.logger = set_eo_gr_logger_for_class(self)

    @cached_property
    def k8s_dns_namespace(self) -> str:
        """DNS server namespace"""
        return self.active_site_config.read_section(GrConfigKeys.DNS_SERVER_NAMESPACE)

    @cached_property
    def active_cluster(self) -> str:
        """Active Site cluster name"""
        return self.active_site_config.read_section(CommonConfigKeys.ENV_NAME)

    @cached_property
    def dns_server_cluster(self) -> str:
        """DNS server cluster name"""
        return self.active_site_config.read_section(
            GrConfigKeys.DNS_SERVER_CLUSTER_NAME
        )

    @cached_property
    def k8s_dns_server_client(self) -> K8sApiClient:
        """K8s client for DNS server"""
        return K8sApiClient(
            namespace=self.k8s_dns_namespace,
            kubeconfig_path=self.active_site_config.read_section(
                GrConfigKeys.DNS_SERVER_KUBE_CONFIG
            ),
            download_location=DEFAULT_DOWNLOAD_LOCATION,
        )

    @cached_property
    def k8s_dns_ip(self) -> str:
        """External server IP (LoadBalancerIP) from config"""
        return self.active_site_config.read_section(
            GrConfigKeys.DNS_SERVER_EX_IP_ADDRESS
        )

    @cached_property
    def active_site_iccr_ip(self) -> str:
        """
        Active site ICCR IP
        Returns:
            The IP of the active site
        """
        return self.active_site_config.read_section(CcdConfigKeys.ICCR_IP)

    @property
    def server_load_balancer_ip(self) -> str:
        """
        Get DNS Service EXTERNAL IP Address (LoadBalancerIP)
        Returns:
            EXTERNAL IP value
        """
        self.logger.info(
            f"Getting EXTERNAL IP (LoadBalancerIP) form {DnsServerK8sConstants.SERVICE_NAME!r} service"
        )
        ext_ip = self.k8s_dns_server_client.get_service_load_balancer_ip(
            service_name=DnsServerK8sConstants.SERVICE_NAME
        )
        self.logger.info(
            f"{DnsServerK8sConstants.SERVICE_NAME!r} service EXTERNAL IP: {ext_ip!r}"
        )
        return ext_ip
