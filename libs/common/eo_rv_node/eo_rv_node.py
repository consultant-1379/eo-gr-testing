"""
Module that stores EO Node relative functionality
"""
import logging

import asyncssh
from core_libs.common.constants import CommonConfigKeys
from core_libs.common.ssh import SSHClient

from libs.common.config_reader import ConfigReader
from libs.utils.logging.logger import logger

logging.getLogger("asyncssh").setLevel(logging.WARNING)


class EoRvNode:
    """
    Class that stores EO Node relative functionality
    """

    def __init__(self, config_reader: ConfigReader):
        self.config_reader = config_reader
        self.ssh_client = SSHClient(
            self.eo_node_host,
            username=self.eo_node_user,
            password=self.eo_node_password,
        )

    @property
    def eo_node_host(self) -> str:
        """EO_NODE_HOST property"""
        return self.config_reader.read_section(CommonConfigKeys.EO_NODE_HOST)

    @property
    def eo_node_user(self) -> str:
        """EO_NODE_USER property"""
        return self.config_reader.read_section(CommonConfigKeys.EO_NODE_USER)

    @property
    def eo_node_password(self) -> str:
        """EO_NODE_PASSWORD property"""
        return self.config_reader.read_section(CommonConfigKeys.EO_NODE_PASSWORD)

    def execute_cmd(self, cmd: str, **kwargs) -> str:
        """
        Execute provided cmd on eo node
        Args:
            cmd: command to execute
            **kwargs: additional SSHClient properties
        Returns:
            cmd output
        """
        logger.info(f"Executing {cmd=} on EO Node")
        with self.ssh_client as ssh_client:
            output = ssh_client.exec_cmd(cmd, stdout_only=False, **kwargs)
        return output.stdout or output.stderr

    async def execute_cmd_async(self, cmd: str, **kwargs) -> str:
        """
        Execute provided cmd on eo node in async mode
        Args:
            cmd: command to execute
            **kwargs: additional SSHClient properties
        Returns:
            cmd output
        """
        logger.info(f"Executing {cmd=} on EO Node")

        async with asyncssh.connect(
            self.eo_node_host,
            username=self.eo_node_user,
            password=self.eo_node_password,
            known_hosts=None,
        ) as conn:
            output = await conn.run(cmd, **kwargs)
        return output.stdout or output.stderr

    def download_file(self, remote_file_path: str, destination_local_path: str) -> None:
        """
        Download file from E0 RV Node to local path
        Args:
            remote_file_path: remote file path
            destination_local_path: local file path
        """
        logger.info(f"Download file {remote_file_path} from EO Node")

        with self.ssh_client as ssh_client:
            ssh_client.download_file(remote_file_path, destination_local_path)
