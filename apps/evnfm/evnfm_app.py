"""
Module with EvnfmApp class
"""
from pathlib import Path
from urllib import parse

from core_libs.common.custom_exceptions import (
    UnexpectedInstanceState,
    UnexpectedOperationType,
)
from core_libs.common.file_utils import FileUtils
from core_libs.common.misc_utils import wait_for
from core_libs.eo.evnfm.evnfm_api import EvnfmApi
from core_libs.eo.evnfm.evnfm_constants import (
    InstantiateFields,
    InstantiateStates,
    Operations,
    OperationState,
    OperationTypes,
)
from core_libs.eo.evnfm.evnfm_test_data import EvnfmTestData
from requests import Response

from apps.evnfm.data.constants import InstanceFields, OperationFields
from libs.common.config_reader import ConfigReader
from libs.common.constants import DEFAULT_DOWNLOAD_LOCATION, EvnfmConfigKeys
from libs.common.custom_exceptions import UnexpectedResponseContentError
from libs.utils.logging.logger import log_exception, logger


class EvnfmApp:
    """
    Class with E-VNFM related operation. Contains general methods for both CVNFM and VMVNFM apps.
    """

    def __init__(self, config: ConfigReader):
        self.config = config
        self.evnfm_test_data = EvnfmTestData()
        self.vnf_lcm_op_occ_id = None
        self.instance_id = None
        self._api = None
        self._default_api = None

    @property
    def hostname(self):
        """Property EVNFM_HOST value"""
        return self.get_hostname(self.config.read_section(EvnfmConfigKeys.EVNFM_HOST))

    @property
    def default_user_name(self):
        """Property EVNFM_DEFAULT_USER_NAME value"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_DEFAULT_USER_NAME)

    @property
    def default_user_password(self):
        """Property EVNFM_DEFAULT_USER_PASSWORD value"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_DEFAULT_USER_PASSWORD)

    @property
    def user_name(self):
        """Property EVNFM_USER_NAME value"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_USER_NAME)

    @property
    def user_password(self):
        """Property EVNFM_USER_PASSWORD value"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_USER_PASSWORD)

    @property
    def tenant(self):
        """Property EVNFM_DEFAULT_TENANT value"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_DEFAULT_TENANT)

    @property
    def pv_storage_class(self):
        """Property PV_STORAGE_CLASS value"""
        return self.config.read_section(EvnfmConfigKeys.PV_STORAGE_CLASS)

    @property
    def api(self) -> EvnfmApi:
        """Property that create connection to EVNFM with non-default user"""
        if not self._api:
            self._api = EvnfmApi(
                url=self.hostname,
                username=self.user_name,
                password=self.user_password,
                tenant=self.tenant,
            )
        return self._api

    @property
    def default_api(self) -> EvnfmApi:
        """Property that create connection to EVNFM with default user"""
        if not self._default_api:
            self._default_api = EvnfmApi(
                url=self.hostname,
                username=self.default_user_name,
                password=self.default_user_password,
                tenant=self.tenant,
            )
        return self._default_api

    @staticmethod
    def get_vnf_lcm_op_occ_id_from_response(response: Response) -> str:
        """
        This is a function which parses requests to get VNFLCM Operation Occurrence Id
        Args:
            response: requests response object

        Returns:
            VNFLCM Operation Occurrence Id
        """
        vnf_lcm_op_occ_id = response.headers["Location"].split("/")[-1]
        logger.info(f"Operation ID: {vnf_lcm_op_occ_id}")
        return vnf_lcm_op_occ_id

    def verify_scale_operation(
        self,
        instance_id: str,
        scale_operation: Operations,
        aspect_id: str,
        start_scale_status: int,
    ) -> None:
        """
        Method to verify base operation steps for Scale In or Scale Out operations

        Args:
            instance_id: id of vmvnfm or cvnfm instance
            scale_operation: operation that performed: either 'Scale In' or 'Scale Out'
            aspect_id: aspect id for which scale operation was done
            start_scale_status: start scale status
        """
        logger.info(f"Verify scale workflow operations after {scale_operation}")

        scale_index = {
            Operations.SCALE_IN: -1,
            Operations.SCALE_OUT: 1,
        }[scale_operation]

        scale_text = "higher" if scale_index > 0 else "less"

        logger.info("Assert that pending operation status is SCALE")
        operation_type = (
            self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
            .json()
            .get(OperationFields.OPERATION)
        )
        assert operation_type == OperationTypes.SCALE, log_exception(
            f"Operation is not SCALE. {operation_type}"
        )
        logger.info("Wait for the Scale operation to be completed")
        self.api.instances_client.wait_for_lcm_operation(self.vnf_lcm_op_occ_id)

        logger.info("Assert that finished operation state is COMPLETED")
        operation_state = (
            self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
            .json()
            .get(OperationFields.OPERATION_STATE)
        )
        assert operation_state == OperationState.COMPLETED, log_exception(
            f"Received operation type is not {OperationState.COMPLETED}"
        )
        logger.info(
            f"Assert that scale status is {scale_text} by 1 than before {scale_operation}."
        )
        end_scale_status = self.api.instances_client.get_scale_value(
            instance_id, aspect_id
        )
        assert (start_scale_status + scale_index) == end_scale_status, log_exception(
            f"End scale status {end_scale_status} is not {scale_text} "
            f"than start scale status of {start_scale_status}"
        )

    @staticmethod
    def get_hostname(url: str) -> str:
        """
        Returns hostname from the url
        Args:
            url: url

        Returns:
            The hostname value, parsed from the url if valid url else initial value
        """
        hostname = parse.urlsplit(url).hostname or url
        logger.debug(f"HOSTNAME: {hostname}")
        return hostname

    def verify_heal_operation(self) -> None:
        """
        Verifies if the HEAL operation performed successfully or not
        Raises:
            UnexpectedOperationType: in case of unexpected operation type
            UnexpectedInstanceState: in case of unexpected instance operation status
        """
        logger.info("Assert that pending operation status is HEAL")
        operation_type = (
            self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
            .json()
            .get(OperationFields.OPERATION)
        )
        if not operation_type == OperationTypes.HEAL:
            raise UnexpectedOperationType(
                log_exception(f"Operation type is not HEAL. {operation_type}")
            )
        logger.info("Wait for the HEAL operation to be completed")
        self.api.instances_client.wait_for_lcm_operation(self.vnf_lcm_op_occ_id)

        logger.info("Assert that finished operation state is COMPLETED")
        operation_state = (
            self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
            .json()
            .get(OperationFields.OPERATION_STATE)
        )
        if not operation_state == OperationState.COMPLETED:
            raise UnexpectedInstanceState(
                log_exception(
                    f"Received operation type is not {OperationState.COMPLETED}"
                )
            )

    @staticmethod
    def download_file(file_path: str) -> Path:
        """
        Download the file to the system
        Args:
            file_path: Path to file
        Returns:
            Local file path
        """
        logger.info(f"Downloading file: {file_path!r}")
        return FileUtils.check_path_for_url(
            file_path, DEFAULT_DOWNLOAD_LOCATION, path_like=True
        )

    def is_package_instantiated(
        self,
        package_id: str,
        check_response: bool = True,
    ) -> None:
        """
        Check if the package is instantiated
        Args:
            package_id: ID of the package
            check_response: True enables response status code check with a specific status code
        Returns:
             None if instantiated, otherwise raises the TimeoutError
        """
        logger.info(
            f"Verifying Instantiation operation status for package ID {package_id!r}"
        )
        instantiate_status = None

        def check_instance_status():
            nonlocal instantiate_status
            instantiate_status = (
                self.api.instances.get_instance_by_id(
                    package_id, check_response=check_response
                )
                .json()
                .get(InstanceFields.INSTANTIATION_STATE)
            )
            return instantiate_status == InstantiateStates.INSTANTIATED

        wait_for(
            check_instance_status,
            interval=5.0,
            timeout=120,
            exc_msg=f"Instantiation has got an unexpected state! {instantiate_status!r}",
        )

    def is_instance_exists(self, descriptor_id: str) -> bool:
        """
        Check if E-VNFM instance exists
        Args:
            descriptor_id: VNFD ID
        Returns:
            True if instance exists else False
        """
        instance_list = self.api.instances_client.get_instances_by_vnfd(descriptor_id)
        return bool(instance_list)

    def get_ve_vnf_instance_by_vnfd_id(
        self, vnfd_id: str, is_unique: bool = False
    ) -> dict | list:
        """
        Get VE-VNF instance by its VNFD ID
        Args:
            vnfd_id: VNFD ID
            is_unique: checking if only one unique instance exists with provided vnfd id
        Raise:
            UnexpectedResponseContentError: if is_unique=True and more than 1 instance with provided vnfd id is found
        Returns:
            instance object or empty list if no one is found
        """
        logger.info(f"Search VE-VNF instances with {vnfd_id=}")
        instances = [
            instance
            for instance in self.api.instances.get_ve_vnf_instances().json()
            if instance.get(InstantiateFields.VNFD_ID) == vnfd_id
        ]
        if is_unique and len(instances) > 1:
            raise UnexpectedResponseContentError(
                log_exception(
                    f"More than 1 instance with {vnfd_id=} exists: {instances}"
                )
            )
        return instances and instances.pop()
