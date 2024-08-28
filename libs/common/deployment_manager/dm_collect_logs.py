"""Module to store DeploymentManagerLogCollection class"""

from functools import cached_property

from core_libs.common.console_commands import CMD
from core_libs.common.constants import CcdConfigKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.config_reader import ConfigReader
from libs.common.deployment_manager.deployment_manager_client import (
    DeploymentManagerClient,
)
from libs.common.deployment_manager.dm_constants import (
    DeploymentManagerCmds,
    DeploymentManagerPatterns,
)
from libs.common.env_variables import ENV_VARS
from libs.common.eo_rv_node.constants import EoNodePaths
from libs.utils.common_utils import run_shell_cmd, search_with_pattern
from libs.utils.logging.logger import logger
from libs.common.constants import LOCAL_LOG_DIR


class DeploymentManagerLogCollection(DeploymentManagerClient):
    """Class with Deployment Manager log collection functionality"""

    def __init__(self, config: ConfigReader):
        super().__init__(config=config, rv_setup=True)
        self.namespace = self._config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE)
        self._eo_node_log_dir = EoNodePaths.LOG_DIR.format(
            env_name=self.workdir_env_name
        )
        self.eo_node_logs = []
        self.downloaded_logs = []
        self.kube_config_path = config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH)

    @cached_property
    def k8s_eo_client(self) -> K8sApiClient:
        """
        K8s EO client property
        Returns: K8sApiClient instance
        """
        return K8sApiClient(
            namespace=self.namespace,
            kubeconfig_path=self.kube_config_path,
        )

    async def exec_dm_collect_logs_cmd(self, namespace: str | None = None) -> str:
        """
        Exec Deployment Management 'collect-logs' command
        Args:
            namespace: a namespace name
        Returns:
            command output
        """
        logger.info("Executing DM 'collect-logs' cmd on EO Node")
        ns = namespace or self.namespace
        dm_command = DeploymentManagerCmds.COLLECT_LOGS.format(namespace=ns)

        return await self.run_dm_docker_cmd_async(dm_command, timeout=5 * 60)

    @staticmethod
    def _scrape_log_file_name_from_output(output: str, pattern: str) -> str | None:
        """Get log archive file name from DM command output
        Args:
            output: DM command output
            pattern: regex pattern for search log file name
        Returns:
            log archive file name
        """
        if log_file_name := search_with_pattern(pattern, output):
            logger.info(f"Log file name found: {log_file_name}")
            return log_file_name

        logger.error(f"Log file name is not found in DM output:\n{output}")
        return None

    def download_all_logs(self) -> None:
        """Download all files from workdir_env/logs"""
        self.create_local_logs_dir()
        logger.info(f"Get all files from {self._eo_node_log_dir}")
        files = self.eo_rv_node.execute_cmd(CMD.LS.format(self._eo_node_log_dir))

        if not files:
            logger.info("No available logs in workdir!")
            return None

        for file in files.split("\n"):
            local_log_file = LOCAL_LOG_DIR / file
            self.eo_rv_node.download_file(
                f"{self._eo_node_log_dir}{file}", local_log_file
            )
            logger.info(f"File {local_log_file} successfully downloaded")
        return None

    async def generate_and_download_log_files(
        self, namespace: str | None = None
    ) -> None:
        """Generate and download log files from EO Node to local path
        Args:
            namespace: a namespace name
        NOTE: 'collect-logs' command produces two logs:
                - cmd executing info log
                - archive(tgz) file with k8s cluster logs
        """
        logger.info(f"Make a directory to store downloaded logs {LOCAL_LOG_DIR}")
        LOCAL_LOG_DIR.mkdir(exist_ok=True)
        output = await self.exec_dm_collect_logs_cmd(namespace)

        archive_log_name = self._scrape_log_file_name_from_output(
            output, DeploymentManagerPatterns.ARCHIVE_LOG
        )
        cmd_execution_log_name = self._scrape_log_file_name_from_output(
            output, DeploymentManagerPatterns.CMD_EXECUTION_LOG
        )
        for log in archive_log_name, cmd_execution_log_name:
            if log:
                eo_node_file_path = self._eo_node_log_dir + log
                self.eo_node_logs.append(eo_node_file_path)

                local_file_path = LOCAL_LOG_DIR / self._compose_log_name(log)
                logger.info(
                    f"Download {eo_node_file_path!r} file from EO Node to {local_file_path=}"
                )
                self.eo_rv_node.download_file(eo_node_file_path, local_file_path)

                self.downloaded_logs.append(local_file_path.name)

        logger.info(f"Downloaded following logs: {self.downloaded_logs}")

    def _compose_log_name(self, original_log_name: str) -> str:
        """Compose log name with which the log will be stored locally
        Args:
            original_log_name: log name from EO Node
        Return:
            modified log name
        """
        log_name = f"{self.workdir_env_name}_{original_log_name}"

        return f"{ENV_VARS.log_prefix}_{log_name}" if ENV_VARS.log_prefix else log_name

    @staticmethod
    def create_local_logs_dir() -> None:
        """Create local logs dir"""
        logger.info(f"Create a directory to store downloaded logs: {LOCAL_LOG_DIR}")
        run_shell_cmd(CMD.MK_DIR.format(LOCAL_LOG_DIR))

    def delete_log_file_from_eo_node(self) -> None:
        """Delete created log file from EO Node to avoid filling up the system's storage"""
        for log in self.eo_node_logs:
            logger.info(f"Deleting log file {log!r} on EO Node")
            self.eo_rv_node.execute_cmd(CMD.RM.format(log))

    def delete_log_dir(self, log_dir_path: str | None = None) -> None:
        """Delete log directory on EO Node
        Args:
            log_dir_path: custom log dir path. If not provided the default will use.
        """
        log_dir_path = log_dir_path or self._eo_node_log_dir
        logger.info(f"Delete log dir {log_dir_path!r} from workdir")
        self.eo_rv_node.execute_cmd(CMD.RM_R.format(log_dir_path))
        logger.info(f"Log dir {log_dir_path!r} has been successfully deleted")

    async def collect_logs_if_failed_pods(self, namespace: str | None = None) -> None:
        """
        Collects logs from the provided namespace via the DM if there is at least one failed pod
        Args:
            namespace: EO or instance namespace name
        """
        logger.info(f"Collecting {namespace} logs via DM...")
        if failed_pods_list := self.k8s_eo_client.get_failed_pods(namespace=namespace):
            logger.warning(
                f"Found the following failed pods in {namespace}: {failed_pods_list}"
            )
            return await self.generate_and_download_log_files(namespace=namespace)
        logger.info(
            f"No failed pods found. Skipping the log collection for the {namespace=}"
        )
