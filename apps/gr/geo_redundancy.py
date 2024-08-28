"""
Module that contains relative Geographical Redundancy functions
"""
from functools import cached_property

from core_libs.common.constants import CommonConfigKeys
from core_libs.common.misc_utils import wait_for

from apps.gr.data.constants import GrSearchPatterns, GrTimeouts, GeoRecoveryStatuses
from apps.gr.geo_base import GeoBase
from apps.gr.geo_status import GeoStatusApp
from apps.gr.gr_docker_registry_app import GrDockerRegistryApp
from apps.gr.gr_rest.gr_rest_api_client import GrRestApiClient
from libs.common.bur_sftp_server.bur_sftp_server import BurSftpServer
from libs.common.config_reader import ConfigReader
from libs.common.custom_exceptions import (
    GrBackupIdNotFoundError,
    GrRecoveryStatusNotFound,
)
from libs.common.deployment_manager.dm_constants import DeploymentManagerCmds
from libs.common.thread_runner import ThreadRunner
from libs.utils.common_utils import (
    is_pattern_match_text,
    search_with_pattern,
)
from libs.utils.logging.logger import logger


class GeoRedundancyApp(GeoBase):
    """
    Class that contains relative Geographical Redundancy fields and operations
    """

    def __init__(
        self,
        active_site_config: ConfigReader,
        passive_site_config: ConfigReader,
        rv_setup: bool,
    ):
        super().__init__(active_site_config, passive_site_config, rv_setup=rv_setup)
        self.gr_status = GeoStatusApp(
            active_site_config, passive_site_config, rv_setup=rv_setup
        )
        self._active_site_gr_registry = None
        self._passive_site_gr_registry = None
        self._sftp_server = None

    @property
    def sftp_server(self) -> BurSftpServer:
        """SFTP server property"""
        if not self._sftp_server:
            self._sftp_server = BurSftpServer(self.active_site_config)
        return self._sftp_server

    @property
    def active_site_gr_registry(self) -> GrDockerRegistryApp:
        """Active Site GR docker registry property"""
        if not self._active_site_gr_registry:
            self._active_site_gr_registry = GrDockerRegistryApp(self.active_site_config)
        return self._active_site_gr_registry

    @property
    def passive_site_gr_registry(self) -> GrDockerRegistryApp:
        """Passive Site GR docker registry property"""
        if not self._passive_site_gr_registry:
            self._passive_site_gr_registry = GrDockerRegistryApp(
                self.passive_site_config
            )
        return self._passive_site_gr_registry

    @cached_property
    def api_client_active_site(self) -> GrRestApiClient:
        """GR REST API client of the Active Site"""
        return GrRestApiClient(site_config=self.active_site_config)

    @cached_property
    def api_client_passive_site(self) -> GrRestApiClient:
        """GR REST API client of the Passive Site"""
        return GrRestApiClient(site_config=self.passive_site_config)

    @property
    def active_site_name(self) -> str:
        """Active Site name"""
        return self.active_site_config.read_section(CommonConfigKeys.ENV_NAME)

    @property
    def passive_site_name(self) -> str:
        """Passive Site name"""
        return self.passive_site_config.read_section(CommonConfigKeys.ENV_NAME)

    def verify_gr_availability(
        self, output_pattern: str = GrSearchPatterns.AVAILABILITY_AVAILABLE
    ) -> bool:
        """
        Verifies EO GR availability after the switchover operation
        Args:
            output_pattern: expect str pattern that should be checked in output
        Returns:
            True if the GR availability message has been met, otherwise False
        """
        timeout = GrTimeouts.AVAILABILITY
        interval = 5.0
        exc_msg = f"EO GR hasn't become available after waiting for {int(timeout / 60)} minutes"

        def check_availability() -> bool:
            """
            Checks EO GR availability message in the subprocess output
            Returns:
                True if the expected message has been found, otherwise False
            """
            cmd = DeploymentManagerCmds.GEO_AVAILABILITY.format(
                primary=self.gr_passive_site_host, secondary=self.gr_active_site_host
            )
            output = self.run_dm_docker_cmd(cmd)
            return is_pattern_match_text(output_pattern, output, group=0)

        return wait_for(
            check_availability, timeout=timeout, interval=interval, exc_msg=exc_msg
        )

    def _create_switchover_cmd(
        self,
        backup_id: str | None = None,
    ) -> str:
        """Method to created Switchover CMD depends on provided back id

        Args:
            backup_id: back up id from each switchover required to be run. Defaults to None.

        Returns:
            Switchover cmd
        """
        cmd = (
            DeploymentManagerCmds.SWITCH_OVER_WITH_BACKUP_ID_CMD
            if backup_id
            else DeploymentManagerCmds.SWITCH_OVER_CMD
        )
        return cmd.format(
            new_primary=self.gr_passive_site_host,
            new_secondary=self.gr_active_site_host,
            backup_id=backup_id,
        )

    def make_switchover(
        self,
        *,
        backup_id: str | None = None,
    ) -> str:
        """
        Function that makes switchover operation
        Args:
            backup_id: if backup id provided it will be used for switchover otherwise DM will be decided automatically
        Returns:
            The switchover command output
        """
        logger.info("Execute switchover...")
        switchover_cmd = self._create_switchover_cmd(backup_id)
        stdout_switchover = self.run_dm_docker_cmd(switchover_cmd)
        logger.info("Switchover execution completed")
        return stdout_switchover

    def make_and_verify_switchover(
        self,
        *,
        backup_id: str | None = None,
        output_pattern: str = GrSearchPatterns.SWITCH_OVER_SUCCESS_STATUS,
    ) -> bool:
        """
        Function that makes switchover operation and verifies the output with the provided pattern
        Args:
            backup_id: if backup id provided it will be used for switchover otherwise DM will be decided automatically
            output_pattern: pattern for check switchover output
        Returns:
            True if switchover success else False
        """
        stdout_switchover = self.make_switchover(backup_id=backup_id)
        return is_pattern_match_text(output_pattern, stdout_switchover, group=0)

    async def make_switchover_async(self, backup_id: str | None = None) -> str:
        """
        Function that makes switchover operation in async mode

        Args:
            backup_id: if backup id provided it will be used for switchover otherwise DM will be decided automatically

        Returns:
            Switchover output
        """
        logger.info("Execute switchover...")
        switchover_cmd = self._create_switchover_cmd(backup_id)
        stdout_switchover = await self.run_dm_docker_cmd_async(switchover_cmd)
        logger.info("Switchover execution completed")
        return stdout_switchover

    def make_and_verify_switchover_in_separate_thread(
        self, backup_id: str | None = None, thread_name: str = "SWITCHOVER"
    ) -> ThreadRunner:
        """
        Make switchover in separate python thread
        Args:
            backup_id: if backup id provided it will be used for switchover otherwise DM will be decided automatically
            thread_name: specify thread name if needed
        Returns:
            threading instance with running switchover
        """
        switchover_thread = ThreadRunner(
            target=self.make_and_verify_switchover,
            kwargs={"backup_id": backup_id},
            name=thread_name,
            daemon=True,
        )
        switchover_thread.start()
        return switchover_thread

    def get_backup_id_from_availability(self) -> str:
        """
        Get backup id from availability command output
        Returns:
            backup id
        """
        cmd = DeploymentManagerCmds.GEO_AVAILABILITY.format(
            primary=self.gr_passive_site_host, secondary=self.gr_active_site_host
        )
        output = self.run_dm_docker_cmd(cmd)

        backup_id = search_with_pattern(GrSearchPatterns.BACKUP_ID, output)
        if not backup_id:
            raise GrBackupIdNotFoundError(f"Backup ID can't be found in {output=}")
        return backup_id

    def verify_images_sync_between_registries(self) -> bool:
        """
        Verify images synced between Active and Passive site GR docker registries
        Returns:
            True if properly sync within timeout unless False
        """
        logger.info(
            "Checking if Passive Site GR Docker Registry are properly synced"
            " with Active Site GR Docker Registry"
        )

        def is_passive_site_gr_docker_registry_sync_with_active_site() -> bool:
            """
            Check if Passive Site GR Docker Registry are properly synced
            with Active Site GR Docker Registry.
            Returns:
                True if properly sync unless False
            """
            registries = self.active_site_gr_registry, self.passive_site_gr_registry
            active_site_images, passive_site_images = [
                r.collect_all_images_with_tags() for r in registries
            ]
            result = active_site_images == passive_site_images

            log_msg = (
                f"GR Docker Registry check {'is Successful' if result else 'found missmatch between registries'}:"
                f"\nActive Site ({self.active_site_name}) registry: {active_site_images}"
                f"\nPassive Site ({self.passive_site_name}) registry: {passive_site_images}"
            )

            if result:
                logger.info(log_msg)
            else:
                logger.warning(log_msg)

            return result

        return wait_for(
            is_passive_site_gr_docker_registry_sync_with_active_site,
            timeout=GrTimeouts.IMAGE_SYNC,
            interval=20,
            exc_msg=(
                "Images are not properly synced between Active and Passive sites "
                f"GR docker registries within timeout: {GrTimeouts.IMAGE_SYNC / 60} min"
            ),
        )

    def verify_backup_id_updated_in_availability(self, interval: float = 5.0) -> bool:
        """
        Verify Backup ID is updated in GR Availability cmd output within timeout
        Returns:
            True if backup is updated, raise exception otherwise
        """
        logger.info(
            "Verifying GR backup ID is updated in GR Availability cmd output..."
        )
        init_backup_id = self.get_backup_id_from_availability()

        return wait_for(
            lambda: init_backup_id != self.get_backup_id_from_availability(),
            timeout=GrTimeouts.AVAILABILITY,
            interval=interval,
            exc_msg=f"Backup ID is not updated in GR Availability cmd output "
            f"within timeout {GrTimeouts.AVAILABILITY}",
        )

    def get_recovery_status(self) -> str:
        """
        Make Geo Recovery Status deployment management cmd and get recovery status value from its output
        Raises:
            GrRecoveryStatusNotFound: when recovery status is not found in output
        Returns:
            Recovery status from recovery status cmd output
        """
        logger.info("Executing geo recovery status cmd...")

        cmd = DeploymentManagerCmds.GEO_RECOVERY_STATUS.format(
            recover_site=self.gr_passive_site_host
        )
        output = self.run_dm_docker_cmd(cmd)
        status = search_with_pattern(GrSearchPatterns.RECOVERY_STATUS, output)
        if not status:
            raise GrRecoveryStatusNotFound(
                f"Recovery status is not found for {self.gr_passive_site_host!r} site.\n{output=}"
            )
        return status

    def verify_recovery_status(
        self, expected_status: GeoRecoveryStatuses, timeout: int = 30
    ) -> bool:
        """
        Verify recovery status is match to expected during timeout
        Args:
            expected_status: expected recovery status
            timeout: timeout
        Returns:
            True or False
        """
        logger.info(f"Verify Recovery Status in {expected_status=}")

        def is_recovery_status_expected() -> bool:
            """
            Inner function to match current status with expected
            Returns:
                True or False
            """
            status = self.get_recovery_status()

            if result := status == expected_status:
                logger.info(f"Recovery Status in {expected_status=}")
            else:
                logger.warning(
                    f"Recovery Status not in {expected_status=}. Current status: {status}"
                )
            return result

        return wait_for(
            is_recovery_status_expected,
            timeout=timeout,
            interval=10,
            exc_msg=f"Recovery Status not in {expected_status=}",
        )

    def update_site_recovery_status(self) -> bool:
        """
        Execute and verify update recovery state deployment management cmd
        Returns:
            True if status updated successfully otherwise False
        """
        logger.info("Executing geo update recovery status cmd...")

        cmd = DeploymentManagerCmds.GEO_UPDATE_RECOVERY_STATE.format(
            recover_site=self.gr_passive_site_host
        )
        output = self.run_dm_docker_cmd(cmd)

        expected_msg = GrSearchPatterns.RECOVERABLE_STATUS_AFTER_UPDATE.format(
            cluster=self.gr_passive_site_host
        )
        return is_pattern_match_text(expected_msg, output, group=0)
