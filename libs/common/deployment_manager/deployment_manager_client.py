"""Module for storing DeploymentManagerClient class"""

from functools import cached_property
from re import findall

from core_libs.common.console_commands import CMD
from core_libs.common.constants import CommonConfigKeys

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrEnvVariables, DockerFlags
from libs.common.custom_exceptions import DeploymentManagerVersionError
from libs.common.deployment_manager.dm_constants import (
    DeploymentManagerDockerCmds,
    DeploymentManagerPatterns,
)
from libs.common.env_variables import ENV_VARS
from libs.common.eo_rv_node.constants import EoNodePaths
from libs.common.eo_rv_node.eo_rv_node import EoRvNode
from libs.utils.common_utils import (
    run_shell_cmd_as_process,
    run_shell_cmd_as_process_async,
)
from libs.utils.logging.logger import logger


class DeploymentManagerClient:
    """Class with functionality for interact with Deployment Manager tool"""

    def __init__(self, config: ConfigReader, rv_setup: bool):
        self._config = config
        self._rv_setup = rv_setup
        self._eo_rv_node = None
        self.workdir_env_name = self._config.read_section(CommonConfigKeys.ENV_NAME)

        logger.debug(
            f"{self.__class__.__name__} initialized for {'RV' if self._rv_setup else 'AppsStaging'} setup"
        )

    @property
    def eo_rv_node(self) -> EoRvNode:
        """EO RV Node instance"""
        if not self._eo_rv_node:
            self._eo_rv_node = EoRvNode(self._config)
        return self._eo_rv_node

    @cached_property
    def dm_version(self) -> str:
        """Receiving Deployment Manager version from DEPLOYMENT_MANAGER_VERSION env variable if present
        otherwise from workdir. Used for RV setup only."""
        if ENV_VARS.deployment_manager_version:
            logger.info(
                f"Deployment Manager version is provided by {GrEnvVariables.DEPLOYMENT_MANAGER_VERSION!r}"
                f" env variable: {ENV_VARS.deployment_manager_version}"
            )
            return ENV_VARS.deployment_manager_version

        logger.info(
            f"{GrEnvVariables.DEPLOYMENT_MANAGER_VERSION!r} env variable is not provided."
            " The Deployment Manager version will be obtained directly from workdir."
        )
        return self.get_deployment_manager_version_from_workdir()

    def get_deployment_manager_version_from_workdir(self) -> str:
        """Getting current DM version from environment's workdir
        Raises:
            DeploymentManagerVersionError: when DM version is not found or multiple versions are found.
        Returns:
            DM version
        """
        workdir = EoNodePaths.WORK_DIR.format(env_name=self.workdir_env_name)
        logger.info(f"Defining Deployment Management version from EO Node {workdir}")

        files = self.eo_rv_node.execute_cmd(CMD.LS.format(workdir))

        dm_version = findall(DeploymentManagerPatterns.DM_VERSION, files)

        if not dm_version:
            raise DeploymentManagerVersionError(
                f"DM version is not found in {workdir}, workdir content:\n{files}"
            )
        if len(dm_version) > 1:
            raise DeploymentManagerVersionError(
                f"Multiple DM versions are found in {workdir}: {dm_version}"
            )
        logger.info(f"Deployment Manager version is defined: {dm_version}")
        return dm_version.pop()

    def _generate_dm_cmd(self, cmd: str) -> str:
        """Generate DM command based on inputs
        Args:
            cmd: DM command
        Returns:
            DM cmd
        """
        if self._rv_setup:
            if ENV_VARS.dns_server_ip:
                dns_flag = DockerFlags.DNS.format(ENV_VARS.dns_server_ip)
            else:
                dns_flag = ""

            return DeploymentManagerDockerCmds.DM_DOCKER_CMD_RV.format(
                DNS_FLAG=dns_flag,
                DM_CMD=cmd,
                ENV_NAME=self.workdir_env_name,
                DM_VERSION=self.dm_version,
            )
        return DeploymentManagerDockerCmds.DM_DOCKER_CMD.format(
            DM_CMD=cmd,
            DM_IMG_NAME=ENV_VARS.deployment_manager_docker_image,
            HOST_LOCAL_PWD=ENV_VARS.host_local_pwd,
        )

    def run_dm_docker_cmd(self, cmd: str) -> str:
        """
        Run Deployment Manager docker command
        Args:
            cmd: DM command
        Returns:
            stdout or stderr output depends on where output returns
        """
        logger.info(f"Running Deployment Manager {cmd=} ...")
        dm_docker_cmd = self._generate_dm_cmd(cmd)

        if self._rv_setup:
            return self.eo_rv_node.execute_cmd(dm_docker_cmd)

        return run_shell_cmd_as_process(dm_docker_cmd)

    async def run_dm_docker_cmd_async(self, cmd: str, timeout: int = None) -> str:
        """
        Run Deployment Manager docker command as async process
        Args:
            cmd: DM command
            timeout: timeout for rv setup cmd execution
        Returns:
            stdout or stderr output depends on where output returns
        """
        logger.info(f"Running Deployment Manager {cmd=} in async mode")
        dm_docker_cmd = self._generate_dm_cmd(cmd)

        if self._rv_setup:
            return await self.eo_rv_node.execute_cmd_async(
                dm_docker_cmd, timeout=timeout
            )
        return await run_shell_cmd_as_process_async(dm_docker_cmd)
