"""
Stores a class that allows deploying a docker image with the DNS (dnsmasq) server on the dedicated host
"""
import json
import re
from collections import namedtuple
from pathlib import Path

import yaml
from core_libs.common.console_commands import CMD, DockerCMD
from core_libs.common.constants import CcdConfigKeys, CommonConfigKeys, K8sKeys
from core_libs.common.misc_utils import encode_to_base64_string
from core_libs.common.ssh import SSHClient
from core_libs.eo.ccd.constants import ConfigMapKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    GrConfigKeys,
    EvnfmConfigKeys,
    DEFAULT_DOWNLOAD_LOCATION,
    UTF_8,
)
from libs.common.dns_server.base_dns import BaseDns
from libs.common.dns_server.data.dns_constants import (
    DnsServerPaths,
    DnsFileConstants,
)

SiteData = namedtuple("SiteData", "env_name k8s_client config")


class DNSServerDeployer(BaseDns):
    """Allows deploying DNS (dnsmasq) service either on the dedicated host as docker container
    or on k8s cluster as deployment."""

    def __init__(
        self,
        active_site_config: ConfigReader,
        passive_site_config: ConfigReader,
        override: list | None = None,
        docker_config_path: str | None = None,
    ) -> None:
        super().__init__(active_site_config=active_site_config)
        self.passive_site_config = passive_site_config

        #  EO configmap constants
        self.namespace = "kube-system"
        self.dns_config_map = self.daemon_set = "node-local-dns"

        # site data
        self.active_site = SiteData(
            env_name=self.active_site_config.read_section(CommonConfigKeys.ENV_NAME),
            k8s_client=self._init_k8s_client(self.active_site_config),
            config=self.active_site_config,
        )
        self.passive_site = SiteData(
            env_name=self.passive_site_config.read_section(CommonConfigKeys.ENV_NAME),
            k8s_client=self._init_k8s_client(self.passive_site_config),
            config=self.passive_site_config,
        )
        # options
        self.override = override or []
        self.docker_config_path = (
            Path(docker_config_path) if docker_config_path else None
        )

        #  DNS server name
        self.dns_service_name = "gr-dnsmasq-service"

        #  DNS config paths
        self.gr_dns_config = "/home/centos/dns_configs"
        self.dns_masq_config_path = (
            self.gr_dns_config + "/" + DnsFileConstants.DNSMASQ_CONF
        )
        self.host_config_path = self.gr_dns_config + "/hosts"

        #  HTTPS prefix
        self.https = "https://"

        #  DNS host docker deploy parameters
        self.docker_dns_ip = self.active_site_config.read_section(
            GrConfigKeys.DNS_CLIENT_HOST
        )
        self.dns_host_user = self.active_site_config.read_section(
            GrConfigKeys.DNS_CLIENT_USER
        )
        self.dns_host_password = self.active_site_config.read_section(
            GrConfigKeys.DNS_CLIENT_PASSWORD
        )
        #  DNS k8s deploy parameters
        self.docker_registry_secret_name = "dawn-img-reg-key"

        #  Docker image of the DNS server
        self.dns_docker_image = self.active_site_config.read_section(
            CommonConfigKeys.DNS_DOCKER_IMAGE
        )
        #  Hosts and IP for the DNS masquerading
        self.docker_registry_host = self.active_site_config.read_section(
            CcdConfigKeys.DOCKER_REGISTRY_HOST
        )
        self.helm_registry_host = self.active_site_config.read_section(
            CcdConfigKeys.HELM_REGISTRY_HOST
        ).removeprefix(self.https)
        self.evnfm_host = self.active_site_config.read_section(
            EvnfmConfigKeys.EVNFM_HOST
        ).removeprefix(self.https)
        self.eo_gas_host = self.active_site_config.read_section(
            CcdConfigKeys.EO_GAS_HOST
        )
        self.global_registry_host = self.active_site_config.read_section(
            CcdConfigKeys.GLOBAL_REGISTRY_HOST
        )

    @property
    def ssh_client(self) -> SSHClient:
        """
        SSH client for the active site
        Returns:
            SSHClient instance
        """
        return SSHClient(
            hostname=self.docker_dns_ip,
            username=self.dns_host_user,
            password=self.dns_host_password,
        )

    @property
    def active_site_domain(self) -> str:
        """
        Active site EVNFM host domain
        Returns:
            The domain of the active site EVNFM host
        """
        return self.evnfm_host.removeprefix("evnfm.")

    @property
    def passive_site_iccr_ip(self) -> str:
        """
        Passive site ICCR IP
        Returns:
            The IP of the passive site
        """
        return self.passive_site_config.read_section(CcdConfigKeys.ICCR_IP)

    @property
    def global_dns_ip(self) -> str:
        """
        Global DNS IP
        Returns:
            The Global Ericsson DNS IP
        """
        return self.active_site_config.read_section(CommonConfigKeys.GLOBAL_DNS_IP)

    @property
    def hosts(self) -> dict:
        """
        Hosts property - default hosts to be masqueraded
        Returns:
            A dictionary with the following structure {<host>: <IP>,...}
        """
        _hosts = {
            self.docker_registry_host: self.active_site_iccr_ip,
            self.helm_registry_host: self.active_site_iccr_ip,
            self.evnfm_host: self.active_site_iccr_ip,
            self.eo_gas_host: self.active_site_iccr_ip,
            self.global_registry_host: [
                self.active_site_iccr_ip,
                self.passive_site_iccr_ip,
            ],
        }
        _hosts.update(self.override_hosts())
        return _hosts

    def _init_k8s_client(
        self,
        config: ConfigReader,
    ) -> K8sApiClient:
        """
        Initialize k8s client
        Args:
            config: config object
        Returns:
            K8sApiClient object
        """
        return K8sApiClient(
            namespace=self.namespace,
            kubeconfig_path=config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH),
            download_location=DEFAULT_DOWNLOAD_LOCATION,
        )

    def override_hosts(self) -> dict:
        """
        Converts a list with passed override hosts and their IP into a dict
        Returns:
            A dictionary with the following structure {<host>: <IP>,...}
        """
        custom_hosts = {}
        for ip_host in self.override:
            ip, host = ip_host.split(":")
            custom_hosts[host] = ip
        return custom_hosts

    def create_dnsmasq_config(self) -> str:
        """
        Prepares dnsmasq config data
        Returns:
            Content for the dnsmasq.conf file
        """
        config_str = ""
        enable_logging = "log-queries\nlog-facility=/var/log/dnsmasq.log\n"
        dns_forward_max = "dns-forward-max=300\n"
        cache_size = "cache-size=0\n"
        for host, ip in self.hosts.items():
            if isinstance(ip, list):
                for i in ip:
                    config_str += f"address=/{host}/{i}\n"
            else:
                config_str += f"address=/{host}/{ip}\n"
        return enable_logging + dns_forward_max + cache_size + config_str

    def add_hosts(self) -> str:
        """
        Forms a string of necessary hosts for starting DNS server container
        Returns:
            A string with custom hosts configuration for the DNS server container
        """
        return " ".join(
            [
                f"--add-host={host}:{ip[0]}"
                if isinstance(ip, list)
                else f"--add-host={host}:{ip}"
                for host, ip in self.hosts.items()
            ]
        )

    def create_hosts_config(self) -> str:
        """
        Prepares data for the /etc/hosts configuration file
        Returns:
            Content for the /etc/hosts file
        """
        ip_hosts = {}
        config_data = ""
        for host, ip in self.hosts.items():
            if isinstance(ip, list):
                ip_hosts.setdefault(ip[0], []).append(host)
            else:
                ip_hosts.setdefault(ip, []).append(host)
        for ip, host_list in ip_hosts.items():
            config_data += f"{ip} {' '.join(host_list)}\n"
        return config_data

    def docker_container_cmd(self) -> str:
        """
        Prepares a command to start a docker container with the DNS server
        Returns:
            Command for launching the DNS server docker container
        """
        return (
            f"docker run {self.add_hosts()} -d "
            f"--name {self.dns_service_name} -p 53:53/udp "
            f"--volume {self.dns_masq_config_path}:/etc/{DnsFileConstants.DNSMASQ_CONF} "
            f"--cap-add=NET_ADMIN {self.dns_docker_image}"
        )

    def form_dns_cm_data(self, dns_ip: str, site: SiteData) -> str:
        """
        Creates a string for the EO configmap DNS configuration
        Args:
            dns_ip: DNS server IP address
            site: SiteData object
        Returns:
            A string with EO DNS configmap configuration
        """
        cluster_local_dns = self._get_cluster_local_dns_ip(site=site)
        return (
            f"{self.active_site_domain}"
            ":53 {\n"
            "    errors\n"
            "    cache {\n"
            "        success 9984 10\n"
            "        denial 9984 5\n"
            "    }\n"
            "    reload\n"
            "    loop\n"
            f"    bind {cluster_local_dns}\n"
            f"    forward . {dns_ip}\n"
            "    prometheus :9253\n"
            "    }\n"
        )

    def patch_config_map(self, dns_ip: str) -> None:
        """
        Patches EO configmap with the custom DNS server parameters
        Args:
            dns_ip: DNS server IP address
        """
        self.logger.info(
            f"Updating {self.dns_config_map!r} configmaps on both "
            f"{self.active_site.env_name!r} and {self.passive_site.env_name!r} clusters..."
        )
        for site in self.active_site, self.passive_site:
            self.logger.info(
                f"Update {self.dns_config_map!r} configmaps on {site.env_name!r}"
            )
            dns_cm_data = self.form_dns_cm_data(dns_ip=dns_ip, site=site)
            dns_config_map_data = site.k8s_client.get_configmap(
                name=self.dns_config_map
            ).data
            if (
                self.active_site_domain
                not in dns_config_map_data[ConfigMapKeys.COREFILE]
            ):
                dns_config_map_data[ConfigMapKeys.COREFILE] += dns_cm_data
                site.k8s_client.patch_configmap(
                    name=self.dns_config_map, data=dns_config_map_data
                )
                self.logger.info(
                    f"Completed! The config map {self.dns_config_map} is successfully updated!"
                )

    def cleanup_config_map_patched_data(self) -> None:
        """
        Cleans up patched data form the EO configmap with the custom DNS server parameters
        and restores the original configmap settings.
        """
        self.logger.info(
            f"Starting to restore {self.dns_config_map!r} configmaps on both "
            f"{self.active_site.env_name!r} and {self.passive_site.env_name!r} clusters..."
        )
        for site in self.active_site, self.passive_site:
            self.logger.info(
                f"Cleanup {self.dns_config_map!r} configmaps on {site.env_name!r}"
            )
            dns_cm_data = site.k8s_client.get_configmap(name=self.dns_config_map).data
            dns_cm_corefile = dns_cm_data[ConfigMapKeys.COREFILE]
            if self.active_site_domain in dns_cm_corefile:
                cm_reg_exp = r"(?P<cm>(\n|.)*?)" + self.active_site_domain
                result = re.search(cm_reg_exp, dns_cm_corefile)
                original_cm_data = result.groupdict().get("cm")
                dns_cm_data[ConfigMapKeys.COREFILE] = original_cm_data
                site.k8s_client.patch_configmap(
                    name=self.dns_config_map, data=dns_cm_data
                )
                self.logger.info(
                    f"Completed! The config map {self.dns_config_map} is successfully restored to the initial state!"
                )
            else:
                self.logger.info(
                    f"Nothing to clean up. The config map {self.dns_config_map} "
                    f"does not contain {self.active_site_domain}:\n{dns_cm_data}"
                )

    def remove_docker_server(self) -> None:
        """
        Removes the container with the configured DNS server and
        cleans up the config map changes on the active site
        """
        self.cleanup_config_map_patched_data()
        with self.ssh_client as ssh:
            self.logger.info(f"Cleaning up {self.gr_dns_config} directory")
            ssh.exec_cmd(CMD.RM_R.format(self.gr_dns_config))
            ssh.exec_cmd(CMD.MK_DIR.format(self.gr_dns_config))

            self.logger.info(
                f"Getting the ID of {self.dns_service_name} container if it exists"
            )
            container_id = ssh.exec_cmd(
                DockerCMD.GET_CONTAINER_ID.format(container_name=self.dns_service_name)
            )
            container_status = (
                f"The container with name {self.dns_service_name} hasn't been found"
            )
            if container_id:
                container_status = f"Stopping and removing {self.dns_service_name} container with ID {container_id}"
                ssh.exec_cmd(DockerCMD.STOP_CONTAINER.format(container_id=container_id))
                ssh.exec_cmd(DockerCMD.RM_CONTAINER.format(container_id=container_id))
            self.logger.info(container_status)

    def deploy_server_as_docker_container(self) -> None:
        """
        The main function that performs DNS server configuration
        """
        self.logger.info(
            f"Configuring DNS server on {self.docker_dns_ip} with {self.active_site.env_name!r} "
            f"hosts settings and {self.passive_site.env_name!r} ICCR IP"
        )
        self.remove_docker_server()
        with self.ssh_client as ssh:
            self.logger.info("Preparing dnsmasq.conf and hosts configuration files")
            ssh.exec_cmd(
                CMD.ECHO_TO_FILE.format(
                    self.create_dnsmasq_config(), self.dns_masq_config_path
                )
            )
            ssh.exec_cmd(
                CMD.ECHO_TO_FILE.format(
                    self.create_hosts_config(), self.host_config_path
                )
            )

            self.logger.info(
                f"Starting dnsmasq container with {self.active_site.env_name!r} hostnames "
                f"and {self.passive_site.env_name!r} ICCR IP configurations"
            )
            ssh.exec_cmd(self.docker_container_cmd())
            self.logger.info(
                f"Completed! The DNS server with {self.active_site.env_name!r} hostnames "
                f"and {self.passive_site.env_name!r} ICCR IP is successfully configured!"
            )

        self.patch_config_map(dns_ip=self.docker_dns_ip)
        self.logger.info("Completed! The DNS server is successfully deployed!")

    def deploy_server_as_k8s_deployment(self) -> None:
        """Deploy DNS server as k8s deployment:
        - remove existed DNS server (if exists)
        - clean up DNS configmap for both sites
        - create k8s namespace
        - create configmap with dnsmasq.conf data
        - create a secret for access to the Docker registry
        - create k8s deployment with DNS server
        - create k8s service for deployment
        - patch DNS configmap on an Active Site with new DNS settings
        """
        self.remove_and_clean_up_dns_k8s_server()

        self.logger.info(
            f"Starting to deploy DNS server as k8s deployment in {self.k8s_dns_namespace!r} ns "
            f"in {self.dns_server_cluster!r} cluster with external DNS IP: {self.k8s_dns_ip}"
        )
        self.logger.info(f"Creating {self.k8s_dns_namespace!r} ns for DNS server")
        self.k8s_dns_server_client.create_namespace(self.k8s_dns_namespace)

        self._create_k8s_configmap_with_dnsmasq_conf()

        self.create_docker_registry_secret()

        self._create_k8s_deployment_with_dns_server()

        self._create_k8s_service_for_dns_deployment()

        self.patch_config_map(dns_ip=self.k8s_dns_ip)

        self.logger.info(
            f"DNS server has been successfully deployed on {self.dns_server_cluster!r} cluster"
            f" and available by {self.k8s_dns_ip!r} IP, "
            f"with the following configuration:\n{self.create_dnsmasq_config()}"
        )

    def _create_k8s_configmap_with_dnsmasq_conf(self) -> None:
        """Create k8s configmap with dnsmasq.conf and "resolv.conf" files data
        to mount them as volumes to DNS server deployment"""
        dnsmasq_conf_data = self.create_dnsmasq_config()
        resolv_conf_data = f"nameserver {self.global_dns_ip}\n"

        with DnsServerPaths.DNS_CONFIGMAP.open(encoding=UTF_8) as f:
            configmap_conf = yaml.safe_load(f)

        configmap_conf[K8sKeys.DATA][DnsFileConstants.DNSMASQ_CONF] = dnsmasq_conf_data
        configmap_conf[K8sKeys.DATA][DnsFileConstants.RESOLV_CONF] = resolv_conf_data

        self.logger.info(
            "Creating configmap for DNS deployment server with DNS server's configuration"
        )
        configmap = self.k8s_dns_server_client.create_configmap_from_yaml(
            yaml_obj=configmap_conf
        ).metadata.name
        self.logger.info(f"Configmap {configmap!r} has been created")

    def _create_k8s_deployment_with_dns_server(self) -> None:
        """Create k8s deployment with DNS server"""
        self.logger.info(
            f"Creating k8s deployment with DNS server in {self.k8s_dns_namespace!r} ns"
        )
        with DnsServerPaths.DNS_DEPLOYMENT.open(encoding=UTF_8) as f:
            deployment_conf = yaml.safe_load(f)
        if self.docker_config_path:
            deployment_conf[K8sKeys.SPEC][K8sKeys.TEMPLATE][K8sKeys.SPEC][
                K8sKeys.IMAGE_PULL_SECRET
            ] = [{K8sKeys.NAME: self.docker_registry_secret_name}]
            self.logger.info(
                f"Patched {DnsServerPaths.DNS_DEPLOYMENT} file with {self.docker_registry_secret_name} secret"
            )
        deployment_name = self.k8s_dns_server_client.create_deployment_from_yaml(
            yaml_obj=deployment_conf
        ).metadata.name

        self.k8s_dns_server_client.wait_deployment_is_up(deployment_name)

        self.logger.info(f"{deployment_name!r} deployment has been created")

    def _create_k8s_service_for_dns_deployment(self) -> None:
        """Create K8s service for DNS server"""
        self.logger.info(
            f"Creating K8s service for DNS server in {self.k8s_dns_namespace!r} ns..."
        )
        with DnsServerPaths.DNS_SERVICE.open(encoding=UTF_8) as f:
            service_conf = yaml.safe_load(f)

        service_conf[K8sKeys.SPEC][K8sKeys.LOAD_BALANCER_IP] = self.k8s_dns_ip

        service = self.k8s_dns_server_client.create_service_from_yaml(
            yaml_obj=service_conf
        )
        self.logger.info(f"{service.metadata.name} service has been created")

    def remove_and_clean_up_dns_k8s_server(self) -> None:
        """Remove k8s namespace with DNS server and restore envs DNS configmap to default"""
        self.cleanup_config_map_patched_data()
        self.logger.info(
            f"Trying to remove already existed {self.k8s_dns_namespace!r} ns..."
        )
        self.k8s_dns_server_client.delete_namespace(
            self.k8s_dns_namespace, raise_exc=False
        )
        self.logger.info("DNS server with its data have been successfully removed!")

    def _get_cluster_local_dns_ip(self, site: SiteData) -> str:
        """Get cluster local DNS IP
        Args:
            site: SiteData object
        Returns:
            local cluster DNS IP
        """
        self.logger.info(f"Get local DNS IP of {site.env_name!r} cluster")
        local_ip_arg = "-localip"
        ds = site.k8s_client.read_daemon_set(
            name=self.daemon_set, namespace=self.namespace
        )
        ds_args: list = ds.spec.template.spec.containers[0].args

        if local_ip := ds_args[ds_args.index(local_ip_arg) + 1]:
            self.logger.info(f"Local cluster DNS IP: {local_ip!r}")
            return local_ip

        raise ValueError(f"Local DNS IP is not found in {self.daemon_set!r} daemon set")

    def create_docker_registry_secret(self) -> None:
        """
        Creating the Docker registry secret
        """
        if not self.docker_config_path:
            self.logger.warning(
                f"For creating {self.docker_registry_secret_name} secret, "
                f"please provide a path to the {DnsFileConstants.DOCKER_CONF_JSON} file\n"
                f"Skipping this step..."
            )
        else:
            self.logger.info(
                "Creating a secret for storing the Docker registry credentials"
            )

            with self.docker_config_path.open(mode="r", encoding=UTF_8) as f:
                docker_config_dict = json.load(f)
            docker_config = encode_to_base64_string(json.dumps(docker_config_dict))

            self.k8s_dns_server_client.create_secret(
                name=self.docker_registry_secret_name,
                data={f".{DnsFileConstants.DOCKER_CONF_JSON}": docker_config},
                namespace=self.k8s_dns_namespace,
                file_type=f"kubernetes.io/{DnsFileConstants.DOCKER_CONF_JSON}",
            )
            self.logger.info(
                f"Docker registry secret {self.docker_registry_secret_name} has been successfully created "
                f"and added to {DnsServerPaths.DNS_DEPLOYMENT} file"
            )
