"""Module to store the VmvnfmLogsCollector class"""

from pathlib import Path

from core_libs.common.console_commands import CMD
from core_libs.eo.ccd.k8s_data.pods import VNFLCM_SERVICE

from apps.codeploy.codeploy_app import CodeployApp
from apps.vmvnfm.data.constants import VmvnfmPaths
from libs.common.config_reader import ConfigReader
from libs.common.constants import LOCAL_LOG_DIR, UTF_8
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class VmvnfmLogsCollector:
    """A class for collecting logs from VMVNFM"""

    def __init__(self, config: ConfigReader):
        self._config = config
        self._codeploy = CodeployApp(self._config)
        self.env_name = self._codeploy.env_name
        self.k8s_client = self._codeploy.k8s_eo_client
        self._logger = set_eo_gr_logger_for_class(self)
        self.local_log_dir = self._create_local_directory_to_store_logs()

    def get_and_save_server_log(self) -> None:
        """Get server.log from VMVNFM service pod(s) and save it locally"""
        self.get_and_save_logs(src_path=VmvnfmPaths.SERVER_LOG)

    def get_and_save_workflow_cli_log(self) -> None:
        """Get workflow management cli log from VMVNFM service pod(s) and save it locally"""
        self.get_and_save_logs(
            src_path=VmvnfmPaths.WFMGR_CLI_LOG, name_to_save="wfmgr-cli-log.log"
        )

    def get_and_save_apache_logs(self) -> None:
        """Get all apache2 logs from VMVNFM service pod(s) and save it locally"""
        self.get_and_save_logs(src_path=VmvnfmPaths.APACHE_LOGS, is_directory=True)

    def get_and_save_logs(
        self,
        src_path: Path,
        is_directory: bool = False,
        name_to_save: str | None = None,
    ) -> None:
        """Get log file from VMVNFM service pod(s) by provided path and save it locally
        Args:
            src_path: a source path to the log or directory within the pod.
            is_directory: define if provided path is a directory or not.
                        If True then all logs within the directory will be downloaded.
            name_to_save: a log will be saved with this value otherwise name will be taken from path,
                        applicable only for single log (when is_directory=False).
        """
        # if HA is enabled then multiple server pods exist
        service_pods = self.k8s_client.get_pods_full_names(VNFLCM_SERVICE)

        for pod_name in service_pods:
            if is_directory:
                self._get_and_save_logs_from_directory(src_path, pod_name)
            else:
                self._get_and_save_single_log(src_path, pod_name, name_to_save)

    def _get_and_save_logs_from_directory(self, src_path: Path, pod_name: str) -> None:
        """Get all logs within a directory from the server pod
        Args:
            src_path: a source path to the directory within the pod.
            pod_name: a full name of server pod.
        """
        sub_local_log_dir = self.local_log_dir / self._compose_name_to_save(
            pod_name, src_path.name
        )
        self._logger.debug(
            f"Make sub-directory to store logs from '{pod_name}:{src_path}'"
        )
        sub_local_log_dir.mkdir(exist_ok=True)

        if logs := self._list_log_files_from_pod_dir(src_path, pod_name):
            for log_name in logs:
                src_log_path = src_path / log_name
                dest_log_path = sub_local_log_dir / log_name

                log_content = self._get_log_content_from_pod(src_log_path, pod_name)
                self._save_log_locally(dest_log_path, log_content)
        else:
            self._logger.warning(f"There are no logs in {pod_name}:{src_path}!")

    def _get_and_save_single_log(
        self, src_path: Path, pod_name: str, name_to_save: str | None = None
    ) -> None:
        """Get a single log from the server pod
        Args:
            src_path: a source path to the log within the pod.
            pod_name: a full name of server pod.
            name_to_save: a log will be saved with this value otherwise name will be taken from path.
        """
        log_name = name_to_save or src_path.name
        dest_log_path = self.local_log_dir / self._compose_name_to_save(
            pod_name, log_name
        )
        log_content = self._get_log_content_from_pod(src_path, pod_name)
        self._save_log_locally(dest_log_path, log_content)

    def _get_log_content_from_pod(self, src_log_path: Path, pod_name: str) -> str:
        """Get log's content from service pod
        Args:
            src_log_path: a source path to the log within the pod.
            pod_name: a full pod name.
        Returns:
            log's content
        """
        self._logger.info(
            f"Getting VMVNFM log from '{pod_name}:{src_log_path}' of {self.env_name!r} site"
        )
        return self._exec_in_server_pod(
            CMD.CAT.format(src_log_path.as_posix()), pod_name
        )

    def _list_log_files_from_pod_dir(
        self, src_path: Path, pod_name: str
    ) -> list | None:
        """List of logs within directory on the server pod
        Args:
            src_path: a source path to the directory within the pod.
            pod_name: a full pod name.
        Returns:
            list with logs files if found, None otherwise
        """
        logs = self._exec_in_server_pod(
            CMD.LS.format(src_path.as_posix()), pod_name, log_output=True
        )
        return logs.strip().split("\n") if logs else None

    def _exec_in_server_pod(
        self, cmd: str, pod_name: str, log_output: bool = False
    ) -> str:
        """Exec a cmd on server pod
        Args:
            cmd: unix cmd to execute within the pod
            pod_name: a full pod name.
            log_output: if True the output is logged to the console, otherwise not
        Returns:
            command output
        """
        return self.k8s_client.exec_in_pod(
            cmd=cmd,
            pod=VNFLCM_SERVICE,
            pod_full_name=pod_name,
            log_output=log_output,
            raise_exc=True,
        )

    def _save_log_locally(self, dest_log_path: Path, log_content: str) -> None:
        """Save log content to local file
        Args:
            dest_log_path: a destination path to save log.
            log_content: content of log.
        """
        with dest_log_path.open(mode="w", encoding=UTF_8) as log:
            log.write(log_content)
        self._logger.info(f"Log has been saved locally in {dest_log_path}")

    def _compose_name_to_save(
        self, pod_name: str, src_log_name_or_dir_name: str
    ) -> str:
        """Compose name with which the log or log dir will be stored locally
        Args:
            pod_name: a name of VMVNFM pod from which the log was taken.
            src_log_name_or_dir_name: an origin log name or directory name.
        Returns:
            name to save locally
        """
        log_name = "_".join([self.env_name, pod_name, src_log_name_or_dir_name])
        return f"{ENV_VARS.log_prefix}_{log_name}" if ENV_VARS.log_prefix else log_name

    def _create_local_directory_to_store_logs(self) -> Path:
        """Create local directory to store downloaded logs
        Returns:
            directory path object
        """
        self._logger.debug(
            f"Make a directory to store downloaded logs if not exists {LOCAL_LOG_DIR}"
        )
        LOCAL_LOG_DIR.mkdir(exist_ok=True)
        return LOCAL_LOG_DIR
