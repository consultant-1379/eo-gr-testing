"""Module to store BurSftpServer class"""

from pathlib import Path

import yaml
from core_libs.common.constants import K8sKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.bur_sftp_server.constants import (
    SFTP_SERVER_POD,
    SftpServerConstants,
    BurSftpPaths,
)
from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    DEFAULT_DOWNLOAD_LOCATION,
    GrConfigKeys,
)
from libs.utils.logging.logger import logger


class BurSftpServer:
    """Class with BUR SFTP Server functionality"""

    def __init__(self, config: ConfigReader):
        self.config = config
        self._k8s_client = None

    @property
    def namespace(self) -> str:
        """SFTP namespace"""
        return self.config.read_section(GrConfigKeys.SFTP_NAMESPACE)

    @property
    def cluster_name(self) -> str:
        """SFTP cluster name"""
        return self.config.read_section(GrConfigKeys.SFTP_CLUSTER_NAME)

    @property
    def kubeconfig(self) -> str:
        """K8s config"""
        return self.config.read_section(GrConfigKeys.SFTP_KUBE_CONFIG)

    @property
    def external_service_ip(self) -> str | None:
        """External service IP (LoadBalancerIP) if provided in config"""
        return self.config.read_section(
            GrConfigKeys.SFTP_EXT_IP_ADDRESS, default_value=None
        )

    @property
    def user_name(self) -> str:
        """SFTP server user name"""
        return self.config.read_section(GrConfigKeys.SFTP_USER_NAME)

    @property
    def password(self) -> str:
        """SFTP password"""
        return self.config.read_section(GrConfigKeys.SFTP_PASSWORD)

    @property
    def k8s_client(self):
        """K8s client"""
        if self._k8s_client is None:
            self._k8s_client = K8sApiClient(
                namespace=self.namespace,
                kubeconfig_path=self.kubeconfig,
                download_location=DEFAULT_DOWNLOAD_LOCATION,
            )
        return self._k8s_client

    def __str__(self) -> str:
        """
        A string representation of the object
        Returns:
            Return a string representation of the object
        """
        return f"SFTP server(cluster={self.cluster_name}, namespace={self.namespace})"

    def deploy_server(self):
        """
        Deploy BUR SFTP server for store GR backups:
        - create K8s namespace
        - create service
        - create deployment with SFTP server pod
        """
        logger.info(
            f"Start to deploy BUR SFTP server in {self.namespace!r} namespace"
            f" on the {self.cluster_name!r} cluster"
        )
        self.k8s_client.delete_namespace(self.namespace, raise_exc=False)

        self.k8s_client.create_namespace(self.namespace)

        self.create_service(BurSftpPaths.SERVICE_CONF_FILE)

        deployment_name = self.k8s_client.create_deployment_from_yaml(
            yaml_file=BurSftpPaths.DEPLOYMENT_CONF_FILE
        ).metadata.name
        self.k8s_client.wait_deployment_is_up(deployment_name)

        logger.info(
            f"BUR SFTP server is successfully deployed in {self.namespace!r} namespace"
            f" on the {self.cluster_name!r} cluster"
        )

    def create_service(self, service_yaml: Path) -> None:
        """
        Method for create K8s service for SFTP server
        """
        logger.info("Create K8s service for SFTP server")
        if self.external_service_ip:
            with service_yaml.open() as f:
                service_conf = yaml.safe_load(f)

            service_conf[K8sKeys.SPEC][
                K8sKeys.LOAD_BALANCER_IP
            ] = self.external_service_ip

            self.k8s_client.create_service_from_yaml(yaml_obj=service_conf)
        else:
            self.k8s_client.create_service_from_yaml(yaml_file=service_yaml)

    @property
    def server_load_balancer_ip(self) -> str:
        """
        Get SFTP Service EXTERNAL IP (LoadBalancerIP) value
        Returns:
            EXTERNAL IP value
        """
        logger.info(
            f"Getting EXTERNAL IP form {SftpServerConstants.SERVICE_NAME!r} service"
        )
        ext_ip = self.k8s_client.get_service_load_balancer_ip(
            service_name=SftpServerConstants.SERVICE_NAME
        )
        logger.info(
            f"{SftpServerConstants.SERVICE_NAME!r} service EXTERNAL IP: {ext_ip!r}"
        )
        return ext_ip

    def change_server_replicas(self, replicas: int) -> None:
        """
        Change number of SFTP server replicas
        Args:
            replicas: desired number of replicas
        """
        logger.info(
            f"Changing number of SFTP server {SFTP_SERVER_POD.name!r} replicas to {replicas}"
        )
        self.k8s_client.scale_deployment_replicas(SFTP_SERVER_POD, replicas)

    def exec_cmd_on_sftp_pod(self, cmd: str) -> str:
        """Exec shell cmd on SFTP server pod
        Args:
            cmd: shell cmd
        Returns:
            cmd output
        """
        logger.info(f"Executing {cmd=} on {self}")
        return self.k8s_client.exec_in_pod(pod=SFTP_SERVER_POD, cmd=cmd)
