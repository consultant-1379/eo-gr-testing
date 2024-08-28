"""Module to store DnsChecker class"""

from urllib import parse

from libs.common.constants import (
    GrEnvVariables,
)
from libs.common.custom_exceptions import (
    DnsServerIsNotDeployed,
    WrongDnsIpError,
    DnsSettingsError,
)
from libs.common.dns_server.base_dns import BaseDns
from libs.common.dns_server.data.dns_constants import DSN_SERVER_POD
from libs.common.env_variables import ENV_VARS
from libs.utils.common_utils import get_ip_address_by_host


class DnsChecker(BaseDns):
    """Class for checking DNS configurations"""

    def verify_dns_environment_configuration_prerequisites(self) -> None:
        """
        Verify DNS environment configuration prerequisites if DNS_SERVER_IP env var provided:
        - DNS_SERVER_IP env var == DNS server IP from config for current Site
        - Check if DNS server deployed
        - DNS server IP (LoadBalancer IP) from current deployed server == DNS server IP from config for current Site
        Raises:
            WrongDnsIpError: when provided DNS IP is not corresponded to expected and
                             when DNS server external IP is not corresponded to expected
            DnsServerIsNotDeployed: when DNS server is not deployed
        """
        if not ENV_VARS.dns_server_ip:
            self.logger.info(
                "Skip DNS environment configuration prerequisites check. "
                f"{GrEnvVariables.DNS_SERVER_IP!r} env var is not provided."
            )
            return None

        self.logger.info("Checking DNS environment configuration prerequisites...")

        if ENV_VARS.dns_server_ip != self.k8s_dns_ip:
            raise WrongDnsIpError(
                f"Provided env var {GrEnvVariables.DNS_SERVER_IP}={ENV_VARS.dns_server_ip} is not corresponded "
                f"to expected DNS IP {self.k8s_dns_ip!r} for GR Site: {self.active_cluster!r}! "
                f"Please provide correct DNS IP."
            )

        if not self.k8s_dns_server_client.is_pod_exists(DSN_SERVER_POD):
            raise DnsServerIsNotDeployed(
                f"DNS server {DSN_SERVER_POD.name!r} is not deployed in {self.k8s_dns_namespace!r} ns.! "
                "Please deploy DNS server first."
            )

        current_dns_ip = self.server_load_balancer_ip

        if current_dns_ip != self.k8s_dns_ip:
            raise WrongDnsIpError(
                f"Current DNS server's IP: {current_dns_ip} is not corresponded to "
                f"expected DNS IP {self.k8s_dns_ip!r} for GR Site: {self.active_cluster}! "
                "Please check DNS configuration."
            )

        self.logger.info(
            "DNS environment configuration prerequisites check finished successfully!"
        )
        return None

    def check_resolving_host_with_active_site_ip(self, host: str) -> None:
        """Check if provided host is resolved by DNS with relevant Active Site ICCR IP
        Args:
            host: host to DNS resolve
        Raises:
            DnsSettingsError: if host is resolved with different from Active Site IP
        """
        host = parse.urlsplit(host).hostname
        self.logger.info(f"Checking DNS settings for {host=}...")

        current_ip = get_ip_address_by_host(host)

        if current_ip != self.active_site_iccr_ip:
            raise DnsSettingsError(
                f"DNS settings are incorrect for Active Site {self.active_cluster!r}:"
                f"\nIP address for {host=} is {current_ip!r}, "
                f"but expected {self.active_site_iccr_ip!r}. Please check DNS settings."
            )
        self.logger.info(f"DNS for {host=} is correctly configured.")
