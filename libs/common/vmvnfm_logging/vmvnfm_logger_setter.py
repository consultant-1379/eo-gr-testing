"""Module to store class for setting log level on VMVNFM services"""

import logging

from core_libs.common.misc_utils import wait_for
from core_libs.eo.ccd.k8s_api_client import K8sApiClient
from core_libs.eo.ccd.k8s_data.pods import VNFLCM_SERVICE

from libs.utils.logging.logger import set_eo_gr_logger_for_class

# source:
# https://confluence-oss.seli.wh.rnd.internal.ericsson.com/display/VNFLM/Information+to+be+provided+while+raising+a+support+ticket+or+CSR+or+Bug

# cmds
JBOSS_CLI = "/ericsson/3pp/jboss/bin/jboss-cli.sh"
JBOSS_CLI_EXEC_CMD = "--command={}".format
JBOSS_STATUS = "sudo -E jboss status"

# paths
SUBSYSTEM_LOG_PATH = "/subsystem=logging/logger=com.ericsson.oss.services"

# logging actions
ADD_LOG_LEVEL = "add(level={})".format
WRT_LOG_LEVEL = "write-attribute(name=level,value={})".format

# services
SERVICE_VNFLAF_SDK = "vnflaf.sdk"
SERVICE_VNFLAF = "vnflcm"
WF_EVENT_LISTENER = "vnflcm.jms.listener.WorkflowEventListener"
WF_INCIDENT_HANDLER = "wfs.internal.handler.WorkflowIncidentHandler"


class VmvnfmLogLevelSetter:
    """Class to setting log level for VMVNFM"""

    def __init__(self, k8s_client: K8sApiClient):
        self.k8s_client = k8s_client
        self._log_level = None
        self._logger = set_eo_gr_logger_for_class(self)

    @property
    def log_level(self) -> str | None:
        """Returns log level value"""
        return self._log_level

    def validate_log_level_value(self, log_level: str) -> None:
        """
        Validation method for log level value
        Args:
            log_level: desired log level for VMVNFM
        """
        if isinstance(logging.getLevelName(log_level), str):
            raise ValueError(f"Incorrect log level value provided: {log_level}")
        self._log_level = log_level

    def _set_log_level_for_service(self, service: str, pod_name: str) -> str | None:
        """
        Function for set log level for VMVNFM service
        Args:
            service: VMVNFM service
            pod_name: vnflcm-service pod name
        Returns:
            error output if an error occurred while setting log level else None
        """
        self._logger.debug(f"Setting {self.log_level=} for {service=}...")

        service_path = f"{SUBSYSTEM_LOG_PATH}.{service}"
        cmd = JBOSS_CLI_EXEC_CMD(service_path)

        output = self._execute_cmd_in_service_pod(
            cmd=f"{cmd}:{ADD_LOG_LEVEL(self.log_level)}", pod_name=pod_name
        )

        if self._is_log_level_successfully_set(output, service):
            return None

        if "failed" in output and "duplicate resource" in output:
            # when log level is already added, then need to exec log write cmd
            output = self._execute_cmd_in_service_pod(
                cmd=f"{cmd}:{WRT_LOG_LEVEL(self.log_level)}",
                pod_name=pod_name,
            )
            if self._is_log_level_successfully_set(output, service):
                return None

        return f"Log level for {service=} is not changed\n{output=}"

    def _execute_cmd_in_service_pod(
        self, cmd: str, pod_name: str, timeout: int = 180, jboss_shell: bool = True
    ) -> str:
        """
        Execute command in VMVNFM service pod
        Args:
            cmd: command to execute
            pod_name: vnflcm-service pod name
            timeout: time to wait for a pod and its containers to up before raising an exception
            jboss_shell: true if needed to use jboss shell instead of default
        Returns:
            command output
        """
        return self.k8s_client.exec_in_pod(
            pod=VNFLCM_SERVICE,
            cmd=cmd,
            pod_full_name=pod_name,
            custom_shell=JBOSS_CLI if jboss_shell else None,
            timeout=timeout,
        ).lower()

    def _is_log_level_successfully_set(self, output: str, service: str) -> bool:
        """
        Check if log level is set successfully
        Args:
            output: console output
            service: VMVNFM service
        Returns:
            True if success unless False
        """
        if "success" in output:
            self._logger.debug(
                f"Log level for {service=} changed -> {self.log_level!r}"
            )
            return True
        return False

    def _is_jboss_running(self, pod_name: str) -> None:
        """Check if jboss service is running. Waiting 360 seconds until running status is received.
        Args:
            pod_name: name of pod
        """
        self._logger.info(f"Check if jboss service is running on {pod_name=}")

        def is_running() -> bool:
            """Check if jboss service is running
            Returns:
                True if running, otherwise False
            """
            output = self._execute_cmd_in_service_pod(
                pod_name=pod_name, cmd=JBOSS_STATUS, jboss_shell=False
            )
            return "jboss-as is running" in output

        wait_for(
            is_running,
            timeout=360,
            interval=10.0,
            exc_msg=f"'jboss' service is not running on {pod_name!r} pod. Failed to changing debug level for VMVNFM",
        )

    def set_log_level(self, log_level: str = "DEBUG") -> None:
        """
        Method for setting logging level for VMVNFM services
        Args:
            log_level: desired log level for VMVNFM, for example: DEBUG, INFO..
        """
        self.validate_log_level_value(log_level)

        self._logger.info(
            f"Start setting log level: {self.log_level!r} for VMVNFM services..."
        )
        errors = []

        service_pods = self.k8s_client.get_pods_full_names(VNFLCM_SERVICE)

        for pod_name in service_pods:
            self._is_jboss_running(pod_name)

            self._logger.debug(f"Performing set level commands on {pod_name!r} pod")

            for service in [
                SERVICE_VNFLAF_SDK,
                SERVICE_VNFLAF,
                WF_EVENT_LISTENER,
                WF_INCIDENT_HANDLER,
            ]:
                if result := self._set_log_level_for_service(service, pod_name):
                    errors.append(result)

        if errors:
            self._logger.error("Log setting is failed with following errors:")
            for error in errors:
                self._logger.error(error)
            raise RuntimeError(
                "Errors occurred during setting log level. See logs above for more details"
            )
        self._logger.info(
            f"VMVNFM log level successfully changed. New Log level -> {self.log_level!r}"
        )
