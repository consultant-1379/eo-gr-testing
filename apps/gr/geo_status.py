"""
Module that contains relative Geographical Redundancy Status functions
"""
from core_libs.common.misc_utils import wait_for

from apps.gr.geo_base import GeoBase
from apps.gr.data.constants import (
    GrSearchPatterns,
    GrTimeouts,
    GrStatusKeys,
    GrStatusSiteInfoStates,
)
from libs.common.deployment_manager.dm_constants import DeploymentManagerCmds
from libs.common.custom_exceptions import (
    GrStatusOutputError,
    GrStatusOutputMissmatchError,
)
from libs.utils.common_utils import search_with_pattern, get_datetime_from_str
from libs.utils.logging.logger import logger, log_exception


class GeoStatusApp(GeoBase):
    """
    Class that contains relative Geo Status fields and operations
    """

    def make_and_verify_geo_status_command(self) -> bool:
        """
        Execute Deployment Manager GR Status command and verify output is match conditions for switchover:
        - Active Apps are the same on both Active and Passive sites
        - Cluster EO version is the same on both Active and Passive sites
        - Backup ID is the same on both Active and Passive sites
        - Image synchronization was successful and match the following: Active timestamp < Passive timestamp

        Making retry during 15 min if GR Status does not match conditions for backup or image sync
        in other cases will rise exception

        Returns:
            True if successful GR Status conditions else False
        """

        def make_and_verify_geo_status() -> bool:
            """
            Inner function for Making GR Status Deployment Manager command
            and verify output is match conditions for switchover.
            Returns:
                True if all conditions are match else False
            """
            logger.info("Executing Geo Status ...")
            geo_status = self.run_dm_docker_cmd(DeploymentManagerCmds.GEO_STATUS_CMD)

            # parse details for Primary and Secondary sites
            primary_details = search_with_pattern(
                GrSearchPatterns.PRIMARY_DETAILS, geo_status, dotall=True
            )
            secondary_details = search_with_pattern(
                GrSearchPatterns.SECONDARY_DETAILS, geo_status, dotall=True
            )
            self.verify_active_apps_are_same_in_geo_status_for_both_sites(
                primary_details, secondary_details
            )
            self.verify_cluster_version_same_in_geo_status_for_both_sites(
                primary_details, secondary_details
            )
            return self.is_backup_same_in_geo_status_for_both_sites(
                primary_details, secondary_details
            ) and self.is_images_sync(primary_details, secondary_details)

        return wait_for(
            condition=make_and_verify_geo_status,
            timeout=GrTimeouts.IMAGE_SYNC,
            interval=30,
            exc_msg="GR Status does not match switchover conditions",
        )

    def geo_status_if_primary_not_alive(self) -> bool:
        """
        Execute Deployment Manager GR Status command when primary site are not available
        and verify output is match conditions for switchover:
        - Primary details are not available

        Making retry during 15 min if GR Status does not match conditions for backup or image sync
        in other cases will rise exception

        Returns:
            True if successful GR Status conditions else False
        """

        def make_and_verify_geo_status() -> bool:
            """
            Inner function for Making GR Status Deployment Manager command
            and verify output is match conditions for switchover.
            Returns:
                True if all conditions are match else False
            """
            exp_msg = "No Primary Details Found"

            geo_status = self.run_dm_docker_cmd(DeploymentManagerCmds.GEO_STATUS_CMD)
            self.verify_active_site_host_match_dns_entry(
                geo_status, GrStatusSiteInfoStates.FAILED
            )

            active_site_details = search_with_pattern(
                GrSearchPatterns.PRIMARY_DETAILS, geo_status, dotall=True
            )
            return exp_msg in active_site_details

        return wait_for(
            condition=make_and_verify_geo_status,
            timeout=GrTimeouts.IMAGE_SYNC,
            interval=30,
            exc_msg="GR Status does not match switchover conditions",
        )

    @staticmethod
    def _search_geo_status_value_by_key(key: str, details: str) -> str:
        """
        Search value by provided key in GR Status output
        Raises:
            GrStatusOutputError: when key is missing in output
        Returns:
            value for provided key
        """
        if result := search_with_pattern(GrSearchPatterns.BY_KEY.format(key), details):
            return result

        raise GrStatusOutputError(
            log_exception(f"Value for {key!r} is missing in GR Status output")
        )

    def verify_active_site_host_match_dns_entry(
        self, geo_status: str, expected_status: str = GrStatusSiteInfoStates.OK
    ) -> None:
        """
        Check Active Site GR Host matches DNS Entry is OK
        Args:
            geo_status: GR Status command output
            expected_status: expected GR status
        Raise:
            GeoStatusOutputMissmatchError: when Active Site GR Host matches DNS Entry is not OK
        """
        logger.info("Start verifying GR Status output")
        host_match = self._search_geo_status_value_by_key(
            GrStatusKeys.HOST_MATCH, geo_status
        ).strip()

        if host_match != expected_status:
            raise GrStatusOutputMissmatchError(
                log_exception(f"{GrStatusKeys.HOST_MATCH} is {host_match}")
            )
        logger.info(f"{GrStatusKeys.HOST_MATCH} is {host_match}")

    def verify_active_apps_are_same_in_geo_status_for_both_sites(
        self, primary_details: str, secondary_details: str
    ) -> None:
        """
        Verify Active Applications are the same on both Active and Passive sites
        Args:
            primary_details: active site GR status details
            secondary_details: passive site GR status details
        Raise:
            GeoStatusOutputMissmatchError: when Active Applications are different
        """
        primary_app = self._search_geo_status_value_by_key(
            GrStatusKeys.ACTIVE_APP, primary_details
        )
        secondary_app = self._search_geo_status_value_by_key(
            GrStatusKeys.ACTIVE_APP, secondary_details
        )
        if primary_app != secondary_app:
            raise GrStatusOutputMissmatchError(
                log_exception(
                    f"{GrStatusKeys.ACTIVE_APP} are not the same:"
                    f" {primary_app=} != {secondary_app=}"
                )
            )
        logger.info(f"{GrStatusKeys.ACTIVE_APP} check is successful")

    def verify_cluster_version_same_in_geo_status_for_both_sites(
        self, primary_details: str, secondary_details: str
    ) -> None:
        """
        Verify Cluster Version of EO are the same on Primary and Secondary sites
        Args:
            primary_details: active site GR status details
            secondary_details: passive site GR status details
        Raise:
            GeoStatusOutputMissmatchError: when Cluster Version of EO are different
        """
        primary_cluster_ver = self._search_geo_status_value_by_key(
            GrStatusKeys.CLUSTER_VERSION, primary_details
        )
        secondary_cluster_ver = self._search_geo_status_value_by_key(
            GrStatusKeys.CLUSTER_VERSION, secondary_details
        )
        if primary_cluster_ver != secondary_cluster_ver:
            raise GrStatusOutputMissmatchError(
                log_exception(
                    f"{GrStatusKeys.CLUSTER_VERSION} is not the same: "
                    f"{primary_cluster_ver=} != {secondary_cluster_ver=}"
                )
            )
        logger.info(f"{GrStatusKeys.CLUSTER_VERSION} check is successful")

    def is_backup_same_in_geo_status_for_both_sites(
        self, primary_details: str, secondary_details: str
    ) -> bool:
        """
        Check Backup IDs are the same on both Active and Passive sites
        Args:
            primary_details: active site GR status details
            secondary_details: passive site GR status details
        Raise:
            GeoStatusOutputMissmatchError: when Last Exported Backup not found
        Returns:
            True or False
        """
        last_exp_backup = self._search_geo_status_value_by_key(
            GrStatusKeys.LAST_EXP_BACKUP, primary_details
        )
        last_imp_backup = self._search_geo_status_value_by_key(
            GrStatusKeys.LAST_IMP_BACKUP, secondary_details
        )
        if "not found" in last_exp_backup.lower():
            raise GrStatusOutputMissmatchError(
                log_exception(f"{GrStatusKeys.LAST_EXP_BACKUP}: {last_exp_backup}")
            )

        if last_exp_backup != last_imp_backup:
            logger.warning(
                f"Backup IDs are not the same: {last_exp_backup=} != {last_imp_backup=}"
            )
            return False

        logger.info("Backup IDs check is successful")
        return True

    def is_images_sync(self, primary_details: str, secondary_details: str) -> bool:
        """
        Check Last Successful Image Synchronisation
        Args:
            primary_details: active site GR status details
            secondary_details: passive site GR status details
        Returns:
            True if Image Synchronisation timestamp of Active site less than timestamp of Passive
            otherwise returns False. Also, returns False if Image Synchronisation timestamp has 'never executed' value.
        """
        primary_img_sync = self._search_geo_status_value_by_key(
            GrStatusKeys.IMAGE_SYNC, primary_details
        )
        secondary_img_sync = self._search_geo_status_value_by_key(
            GrStatusKeys.IMAGE_SYNC, secondary_details
        )
        if "never executed" in primary_img_sync.lower():
            logger.warning(
                f"{GrStatusKeys.IMAGE_SYNC}: {primary_img_sync}. Wait for the images to sync"
            )
            return False

        primary_img_sync_dt = get_datetime_from_str(primary_img_sync)
        secondary_img_sync_dt = get_datetime_from_str(secondary_img_sync)

        if primary_img_sync_dt > secondary_img_sync_dt:
            logger.warning(
                f"Image Synchronisation is not match condition: "
                f"{primary_img_sync=} should be less than {secondary_img_sync=}"
            )
            return False

        logger.info("Image Synchronisation check is successful")
        return True
