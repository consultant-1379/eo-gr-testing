""""
Workflow service class
"""
import re
from pathlib import Path

from core_libs.common.constants import CommonConfigKeys
from core_libs.common.misc_utils import wait_for
from core_libs.eo.vmvnfm.vmvnfm_test_data import VmVnfmTestData

from apps.vmvnfm.data.services import WORKFLOW_SERVICE
from libs.utils.logging.logger import logger, log_exception


class WorkflowService:
    """
    WorkflowService class contains all methods related to Workflow and then used as test steps
    """

    def __init__(self, config, vnvnfm_cli):
        self.config = config
        self.vnvnfm_cli = vnvnfm_cli

    @property
    def workflow_package_path(self) -> str:
        """A workflow package location URL property"""
        return self.config.read_section(CommonConfigKeys.WORKFLOW_PATH)

    @property
    def generic_workflow_package_path(self) -> str:
        """A generic workflow package location URL property"""
        return self.config.read_section(CommonConfigKeys.GENERIC_WORKFLOW_PATH)

    def download_rpm_package(self, file_path: str | None = None) -> str:
        """
        Download RPM package for workflow installation
        Args:
            rpm_package_path location
        Returns:
            A path to the downloaded package
        """
        logger.info("Upload rpm file to POD")
        file_path = file_path or self.workflow_package_path
        download_dir = VmVnfmTestData.DEFAULT_DOWNLOAD_FOLDER
        self.vnvnfm_cli.download_file_to_pod(file_path, download_dir)
        rpm_package_path = f"{download_dir}/{Path(file_path).name}"
        return rpm_package_path

    def remove_rpm_package(self, file_path: str) -> None:
        """
        Remove package from POD
        Args:
            file_path: Path to RPM package
        """
        logger.info("Remove rpm file from POD")
        self.vnvnfm_cli.remove_file_from_pod(file_path)

    def install_workflow(self, file_path: str) -> None:
        """
        Install workflow
        Args:
            file_path: Path to RPM package
        """
        logger.info(f"Install workflow with package {file_path} in VM VNFM")
        output_cmd = self.vnvnfm_cli.install_workflow_package(file_path)

        logger.info("Verify workflow installed")
        assert WORKFLOW_SERVICE.add_success_text in output_cmd, log_exception(
            "Workflow package install failed."
        )
        assert self.is_workflow_installed(file_path), log_exception(
            "Installed workflow not in list of available workflows"
        )

    def uninstall_workflow(
        self,
        file_path: str | None = None,
    ) -> None:
        """
        Uninstall workflow
        Args:
            file_path: Package path of the workflow to be removed
        Raises:
            AssertionError: when workflow package uninstallation failed
        """
        logger.info("Uninstall WorkflowService from VM VNFM")
        file_path = file_path or self.workflow_package_path
        file_path = Path(file_path)
        logger.info(f"Uninstall workflow with name {file_path.name}")
        if self.is_workflow_installed(file_path):
            logger.info(f"Uninstall workflow name {file_path.name}")
            output_cmd = self.vnvnfm_cli.uninstall_workflow_package(str(file_path))
            assert WORKFLOW_SERVICE.delete_success_text in output_cmd, log_exception(
                f"{file_path.name} workflow package uninstall failed"
            )
        else:
            logger.info(f"No workflow installed with name: {file_path.name}")

    def is_workflow_installed(
        self, file_path: str | Path | None = None, apply_wait: bool = False
    ) -> bool:
        """
        Checks if workflow installed
        Args:
            file_path: Package path of the workflow to be removed
            apply_wait: Applying a wait to check WF existence in case getting the following
                        "no descriptor details present in db" msg in output to monitor EO-177618 issue.
                        Should be used only in post-switchover phases.
        Returns:
            True if workflow installed else False
        """
        file_path = file_path or self.workflow_package_path
        file_path = file_path if isinstance(file_path, Path) else Path(file_path)
        workflow_name = self.get_workflow_name(file_path)
        workflow_version = self.get_workflow_version(file_path)

        logger.info(f"Check if {workflow_name=} with {workflow_version=} installed.")
        output_cmd = ""

        def exec_cmd() -> str:
            """Exec cli cmd to check WF existence
            Returns:
                cmd output
            """
            nonlocal output_cmd
            output_cmd = self.vnvnfm_cli.list_of_workflows(
                workflow_name, workflow_version
            )
            return output_cmd

        if apply_wait:
            logger.debug("Applying wait to verify WF installation")
            # this wait is implemented to monitoring EO-177618, may need to be changed/removed after issue analysis
            wait_for(
                lambda: "no descriptor details present in db" not in exec_cmd().lower(),
                timeout=3 * 60,
                raise_exc=False,
            )
            return bool(output_cmd.count(workflow_name))
        return bool(exec_cmd().count(workflow_name))

    @staticmethod
    def get_workflow_version(file_path: Path) -> str:
        """
        Retrieves a workflow version from its path
        Args:
            file_path: Package path of the workflow to be removed
        Returns:
            Workflow version
        """
        match = re.search(r"(?<=-)(.*?)(?=.rpm)", file_path.name)
        if match is None:
            raise ValueError(
                f"Can't get workflow version from given URL: {str(file_path)}"
            )
        return match.group(0)

    @staticmethod
    def get_workflow_name(file_path: Path) -> str:
        """
        Retrieves a workflow name from its path
        Args:
            file_path: Package path of the workflow to be removed
        Returns:
            Workflow name
        """
        match = re.search(r"(?<=ERIC)(.*?)(?=_)", file_path.name)
        if match is None:
            raise ValueError(
                f"Can't get workflow name from given URL: {str(file_path)}"
            )
        return match.group(0)
