"""A module to store MasterNode class"""

from functools import cached_property

from core_libs.common.console_commands import HelmCMD
from core_libs.common.constants import CcdConfigKeys, CommonConfigKeys
from core_libs.common.file_utils import FileUtils

from libs.common.config_reader import ConfigReader
from libs.common.constants import DEFAULT_DOWNLOAD_LOCATION
from libs.common.master_node_ssh_client import SSHMasterNode
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class MasterNode:
    """A class to interact with EO Master Node"""

    def __init__(self, config: ConfigReader, ip: str | None = None):
        """Init method
        Args:
            config: config object
            ip: master node IP address, override master node IP from config
        """
        self._config = config
        self._ip = ip
        self._ssh_client = None
        self.worker_ip = None
        self.worker_username = None
        self._logger = set_eo_gr_logger_for_class(self)

    @cached_property
    def ip(self) -> str:
        """
        The EO master node IP
        Returns:
            A master node IP
        """
        return self._ip or self._config.read_section(CcdConfigKeys.MASTER_IP)

    @cached_property
    def username(self) -> str:
        """
        The EO master node username
        Returns:
            The EO Master node username
        """
        return self._config.read_section(CcdConfigKeys.MASTER_USERNAME)

    @cached_property
    def ssh_pkey(self) -> str:
        """
        The EO master node SSH private key
        Returns:
            A path to the downloaded EO master node SSH private key
        """
        remote_path = self._config.read_section(CcdConfigKeys.MASTER_PKEY)
        return FileUtils.check_path_for_url(remote_path, DEFAULT_DOWNLOAD_LOCATION)

    @cached_property
    def cluster_name(self) -> str:
        """
        Cluster name from config
        Returns:
            Cluster name
        """
        return self._config.read_section(CommonConfigKeys.ENV_NAME)

    def set_ssh_client(
        self, *, worker_ip: str | None = None, worker_username: str | None = None
    ) -> SSHMasterNode:
        """
        Establishes an SSH connection to the EO Master node
        Args:
            worker_ip: IP address of the worker node
            worker_username: Worker node username
        Returns:
            An instance of the SSHMasterNode class
        """
        self.worker_ip = self.worker_ip or worker_ip
        self.worker_username = self.worker_username or worker_username

        if not self._ssh_client:
            self._ssh_client = SSHMasterNode(
                self.ip,
                username=self.username,
                key_filename=self.ssh_pkey,
                worker_ip=self.worker_ip,
                worker_username=self.worker_username,
            )
        return self._ssh_client

    def is_nfs_deployment_exists(self, nfs_name: str, namespace: str) -> bool:
        """Check if NFS deployment exists
        Args:
            nfs_name: name of NFS
            namespace: name of NFS namespace
        Returns:
            True if exists, otherwise False
        """
        self._logger.info(
            f"Checking existence of {nfs_name} NFS on {self.cluster_name!r} cluster's master node..."
        )
        with self.set_ssh_client() as ssh:
            return bool(
                ssh.exec_cmd(
                    cmd=HelmCMD.STATUS.format(f"{nfs_name} -n {namespace}"),
                    verify_exit_code=False,
                )
            )

    def add_nfs_repo(self) -> None:
        """Execute cmd to add NFS repo on master node"""
        self._logger.info("Adding NFS provisioner repo...")
        with self.set_ssh_client() as ssh:
            ssh.exec_cmd(
                HelmCMD.REPO_ADD.format(
                    "nfs-subdir-external-provisioner "
                    "https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/"
                )
            )

    def install_nfs(
        self, nfs_name: str, namespace: str, nfs_server_ip: str, storage_class_name: str
    ) -> None:
        """Execute cmd to install NFS deployment on master node
        Note: It is enough to install on only one master node.
        Args:
            nfs_name: name of NFS
            namespace: name of namespace for NFS
            nfs_server_ip: server IP address
            storage_class_name: storage class name
        """
        env_folder = {"ci476": "C15A7", "ci480": "C11A022"}.get(
            self.cluster_name, self.cluster_name.upper()
        )
        self._logger.info("Installing NFS provisioner...")
        with self.set_ssh_client() as ssh:
            ssh.exec_cmd(
                HelmCMD.INSTALL.format(
                    f"{nfs_name} nfs-subdir-external-provisioner/nfs-subdir-external-provisioner "
                    f"--set storageClass.name={storage_class_name} --set nfs.server={nfs_server_ip} "
                    f"--set nfs.path=/nfs/{env_folder} "
                    f"--set storageClass.archiveOnDelete=false -n {namespace}"
                )
            )
