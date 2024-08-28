""" Module with CvnfmApp class"""
import asyncio
from functools import cached_property
from http import HTTPStatus

from core_libs.common.constants import ArtefactConfigKeys
from core_libs.common.constants import CcdConfigKeys
from core_libs.common.csar_utils import CsarUtils
from core_libs.common.custom_exceptions import (
    AssetNotFoundException,
    UnexpectedInstanceState,
)
from core_libs.common.file_utils import FileUtils
from core_libs.common.misc_utils import build_json_from_file, vnfd_parser
from core_libs.eo.constants import ApiKeys
from core_libs.eo.evnfm.evnfm_constants import (
    EvnfmOperations,
    InstantiateFields,
    InstantiateStates,
    Operations,
    OperationTypes,
)

from apps.cvnfm.data.constants import CommonFields
from apps.cvnfm.data.cvnfm_artefact_model import CvnfmArtifactModel
from apps.evnfm.data.constants import (
    InstanceFields,
    OperationFields,
    DEFAULT_EVNFM_APP_TIMEOUT,
)
from apps.evnfm.evnfm_app import EvnfmApp
from libs.common.config_reader import ConfigReader
from libs.common.constants import DEFAULT_DOWNLOAD_LOCATION
from libs.common.custom_exceptions import UnexpectedNumberOfCnfInstances
from libs.common.deployment_manager.dm_collect_logs import (
    DeploymentManagerLogCollection,
)
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import logger, log_exception


class CvnfmApp(EvnfmApp):
    """
    CvnfmApp class contains all methods related to CVNFM and then used as test steps
    """

    def __init__(self, config: ConfigReader):
        super().__init__(config)
        self.cnf_id = None
        self.unsigned_cnf_id = None
        self.vnf_lcm_op_occ_id = None
        self.namespace = None

    @property
    def registry_user_name(self):
        """Get REGISTRY_USER_NAME config value"""
        return self.config.read_section(CcdConfigKeys.REGISTRY_USER_NAME)

    @property
    def registry_user_password(self):
        """Get REGISTRY_USER_PASSWORD config value"""
        return self.config.read_section(CcdConfigKeys.REGISTRY_USER_PASSWORD)

    @cached_property
    def dm_log_collector(self) -> DeploymentManagerLogCollection:
        """
        DM Log Collection property
        Returns:
            DeploymentManagerLogCollection instance
        """
        return DeploymentManagerLogCollection(self.config)

    # region CNF packages

    @cached_property
    def cnf_smallstack_pkg(self) -> CvnfmArtifactModel:
        """
        Returns CNF package used for all operations except upgrade
        :return: CVNFM artefact object
        """
        return self.config.artefacts.get_by_id(ArtefactConfigKeys.CNF_TEST_PACKAGE)

    @cached_property
    def cnf_upgrade_smallstack_pkg(self) -> CvnfmArtifactModel:
        """
        Returns CNF package used for upgrade operation
        :return: CVNFM artefact object
        """
        return self.config.artefacts.get_by_id(ArtefactConfigKeys.CNF_TEST_UPGRADE_PKG)

    @cached_property
    def cnf_unsigned_smallstack_pkg(self) -> CvnfmArtifactModel:
        """
        Returns the unsigned CNF package used for all operations except upgrade
        Returns:
            CVNFM artefact object
        """
        return self.config.artefacts.get_by_id(ArtefactConfigKeys.CNF_TEST_UNSIGNED_PKG)

    # endregion CNF packages

    def download_cnf_package_and_randomize_vnf_id(
        self, package: CvnfmArtifactModel, is_randomize_vnfd: bool = False
    ) -> None:
        """
        Download cnf package and randomaize VNF ID
        :param package: CNF package
        :param is_randomize_vnfd: option for randomize vnfd
        """
        logger.info("Download cnf package file to system")
        package.path = self.download_file(package.url)
        if is_randomize_vnfd:
            CsarUtils.randomize_vnfd_id(package, tmp_dir_path=DEFAULT_DOWNLOAD_LOCATION)

    def onboard_cnf_package(
        self, package: CvnfmArtifactModel, cleanup_pkg: bool = False
    ) -> str:
        """
        Method to onboard package to C-VNFM
        Args:
            package: a package
            cleanup_pkg: deletes package from file system if True
        Return: package id
        """
        logger.info("Onboard package to CVNFM")

        try:
            payload = self.evnfm_test_data.packages_test_data.get_create_vnf_package_resource_json(
                package.onboarding_timeout
            )
            package_id = self.api.packages_client.onboard_csar_package(
                payload, package.path
            )
            package.descriptor_id = self.api.packages_client.find_vnfd_id(package_id)
        finally:
            if cleanup_pkg:
                logger.debug(f"Delete unused package: {package.path}")
                FileUtils.delete_file(package.path)
        return package_id

    def delete_cnf_package_if_exists(self, package_descriptor_id: str) -> None:
        """
        Delete CNF package if it exits
        :param package_descriptor_id: descriptor id
        """
        logger.info(f"Delete CNF package {package_descriptor_id=} if exists")
        package_id = self.api.packages_client.check_if_package_with_vnfd_id_exists(
            package_descriptor_id
        )
        if package_id:
            logger.info(f"Package id to be deleted {package_id!r}")
            self.api.packages.delete_vnf_package(package_id)

    def create_cnf_instance_identifier(
        self, descriptor_id: str, vapp_name: str | None = None
    ):
        """
        Create CNF Instance identifier for onboarded CNF package
        Args:
            descriptor_id: ID of the package descriptor
            vapp_name: VAPP name
        Returns:
            CNF Instance ID
        """

        create_identifier_json = (
            self.evnfm_test_data.instance_test_data.create_vnf_identifier_data(
                descriptor_id, vapp_name=vapp_name
            )
        )
        cnf_id = self.api.instances.create_instance_identifier(
            create_identifier_json
        ).json()["id"]
        return cnf_id

    def instantiate_cnf(
        self, cnf_id: str, package_id: str, cluster_name: str, instance_name: str
    ) -> str:
        """
        Method to deploy CNF instance
        Args:
            cnf_id: cnf id
            package_id: package ID
            cluster_name: Kubernetes cluster name
            instance_name: CNF instance name
        Returns:
            instance ID
        Raises:
            UnexpectedInstanceState in case during deploying some errors happen
        """
        logger.info(f"Instantiate CNF package with {package_id=}")
        instantiate_data = self.get_deploying_data(
            package_id, cluster_name, instance_name
        )

        logger.info(f"Sending Instantiate CNF request for CNF ID {cnf_id}")
        logger.info("Instantiating a CNF instance")
        response = self.api.instances.instantiate_cnf(cnf_id, instantiate_data)
        vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)

        logger.info(
            f"Verifying CNF Lifecycle operation state for vnfLcmOpOccId {vnf_lcm_op_occ_id}"
        )
        try:
            self.api.instances_client.wait_for_lcm_operation(vnf_lcm_op_occ_id)
        except UnexpectedInstanceState as exception:
            if ENV_VARS.is_rv_setup:
                asyncio.run(
                    self.dm_log_collector.collect_logs_if_failed_pods(
                        namespace=instance_name
                    )
                )
            cleanup_json = (
                self.evnfm_test_data.instance_test_data.cleanup_instance_json()
            )
            self.api.instances.clean_up_failed_instance(cnf_id, cleanup_json)
            self.api.instances_client.wait_for_cnf_deletion(cnf_id)
            raise UnexpectedInstanceState(
                f"Unexpected instance state during instantiation. Instance id: {cnf_id}"
            ) from exception
        self.is_package_instantiated(cnf_id)
        return cnf_id

    def get_deploying_data(
        self, package_id: str, cluster_name: str, instance_name: str
    ) -> dict:
        """
        Get deploying data
        Args:
            package_id: Package ID
            cluster_name: Kubernetes cluster name
            instance_name: CNF instance name
        Returns:
            Payload for CNF instantiation
        """
        logger.info("Prepare deploying data")
        if self.cnf_smallstack_pkg.additional_config:
            filename = self.download_file(self.cnf_smallstack_pkg.additional_config)
            data = build_json_from_file(filename)
            logger.debug(f"Additional config provided by user is {data}")
        else:
            vnfd_data = self.api.packages.get_vnfd_data(package_id)
            data = vnfd_parser(
                vnfd_data.text,
                EvnfmOperations.INSTANTIATE,
                storage_class=self.pv_storage_class,
            )
        data = self.update_payload_with_lcm_operation_timeout(data)
        instantiate_data = self.evnfm_test_data.instance_test_data.instantiate_cnf_data(
            cluster_name, instance_name, DEFAULT_EVNFM_APP_TIMEOUT
        )
        self.namespace = instantiate_data[CommonFields.ADDITIONAL_PARAMS][
            CommonFields.NAMESPACE
        ]
        additional_params_data = (
            self.evnfm_test_data.instance_test_data.upd_inst_cnf_with_additional_params(
                self.namespace
            )
        )
        data.update(additional_params_data)
        logger.debug(data)
        instantiate_data.get(CommonFields.ADDITIONAL_PARAMS).update(data)

        return instantiate_data

    def terminate_cnf_instance(
        self, instance_id: str, remove_cnf_identifier: bool = True
    ) -> None:
        """
        Method to delete CNF instance
        Args:
            instance_id: instance ID
            remove_cnf_identifier: remove CNF Identifier
        """
        logger.info(f"Terminate CNF {instance_id=}")
        delete_instance_json = (
            self.evnfm_test_data.instance_test_data.delete_cnf_instance_json(
                application_time_out=DEFAULT_EVNFM_APP_TIMEOUT
            )
        )
        response = self.api.instances.delete_cnf(instance_id, delete_instance_json)
        vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)
        self.api.instances_client.wait_for_lcm_operation(vnf_lcm_op_occ_id)

        if remove_cnf_identifier:
            self.api.instances.delete_instance_identifier(instance_id)

    def update_payload_with_additional_pars(
        self,
        payload: dict,
        operation: str,
        package_id: str,
        is_additional_params: bool = False,
    ) -> dict:
        """
        This function updates the payload if the additional param file provided
        :param payload: the original payload dict to be updated
        :param operation: the operation type (eg. scale, change_package)
        :param package_id: the id of the package to parse the additional parameters from
        :param is_additional_params: Flag that define usage of additional params
        :return: updated payload dict with additional parameters, or empty dict
        """
        additional_pars = {}

        logger.info("Updating payload field: additionalParams")
        if operation == EvnfmOperations.SCALE:
            filename_to_use = (
                self.download_file(self.cnf_smallstack_pkg.additional_config_scale)
                if self.cnf_smallstack_pkg.additional_config_scale
                else None
            )
            logger.debug(
                f"Filename for additional parameters (scale operation): {filename_to_use}"
            )
        elif operation == EvnfmOperations.CHANGE_PACKAGE:
            filename_to_use = (
                self.download_file(self.cnf_smallstack_pkg.additional_config_modify)
                if self.cnf_smallstack_pkg.additional_config_modify
                else None
            )
            logger.debug(
                f"Filename for additional parameters (instantiate operation): {filename_to_use}"
            )
        else:
            logger.error(f"Unknown operation: {operation}")
            return additional_pars

        if filename_to_use is not None:
            try:
                logger.info(f"Get additionalParams from file: {filename_to_use}")
                additional_pars = build_json_from_file(filename_to_use)
                logger.debug(f"Additional config provided by user is {additional_pars}")
            finally:
                logger.debug(f"Delete uploaded file {filename_to_use}")
                FileUtils.delete_file(filename_to_use)
        else:
            if is_additional_params:
                logger.debug("Applying additional params for CNF package")
                additional_pars = self.evnfm_test_data.instance_test_data.upd_inst_cnf_with_additional_params(
                    self.namespace
                )
            else:
                logger.info(
                    "Get additionalParams from package definition (default values)"
                )
                vnfd_data = self.api.packages.get_vnfd_data(package_id)
                additional_pars = vnfd_parser(
                    vnfd_data.text,
                    operation,
                    storage_class=self.pv_storage_class,
                )
        payload.get(CommonFields.ADDITIONAL_PARAMS).update(additional_pars)
        return payload

    def upgrade_vnf_instance(
        self,
        is_additional_params_for_change_pkg: bool,
        cnf_package_id: str,
        cnf_id: str | None = None,
    ) -> None:
        """
        Method to upgrade VNF instance
        Args:
            is_additional_params_for_change_pkg: Flag that define usage of additional params
            cnf_package_id: CNF package ID of the package to be upgraded
            cnf_id: ID of the instantiated CNF package
        """
        logger.info("Upgrading CNF instance")
        upgrade_instance_json = (
            self.evnfm_test_data.instance_test_data.change_cnf_instance_json(
                self.cnf_upgrade_smallstack_pkg.descriptor_id,
                application_time_out=DEFAULT_EVNFM_APP_TIMEOUT,
            )
        )
        upgrade_instance_json = self.update_payload_with_lcm_operation_timeout(
            upgrade_instance_json
        )
        upgrade_instance_json = self.update_payload_with_additional_pars(
            upgrade_instance_json,
            operation=EvnfmOperations.CHANGE_PACKAGE,
            package_id=cnf_package_id,
            is_additional_params=is_additional_params_for_change_pkg,
        )
        cnf_id = cnf_id or self.cnf_id
        response = self.api.instances.change_cnf_instance(cnf_id, upgrade_instance_json)
        assert response.status_code == HTTPStatus.ACCEPTED, log_exception(
            f"Response code is not {HTTPStatus.ACCEPTED}"
        )

        logger.info("Query the life cycle operation status code")
        self.vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)
        response = self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
        logger.info(f"{response}")
        assert response.status_code == HTTPStatus.OK, log_exception(
            f"Response code is not {HTTPStatus.OK}. ERROR : {response.status_code!r}"
        )

        logger.info("Wait for CNF instance Operation State to be Completed")
        self.api.instances_client.wait_for_lcm_operation(self.vnf_lcm_op_occ_id)

    def verify_instance_workflow_operations(self, operation):
        """
        Method to verify base operation steps for Upgrade or Rollback operations
        :param operation: operation that performed: Upgrade or Rollback
        :type operation: str
        :raises AssetNotFoundException: If provided operation is unknown
        """
        logger.info(f"Verify instance workflow operations after {operation}")
        operations = {
            Operations.UPGRADE: self.cnf_upgrade_smallstack_pkg.descriptor_id,
            Operations.ROLLBACK: self.cnf_smallstack_pkg.descriptor_id,
        }

        try:
            descriptor_id = operations[operation]
        except KeyError as e:
            raise AssetNotFoundException(f"No operation with name: {operation}") from e

        logger.info("Verify Operation is Change VNF Package")
        operation_type = (
            self.api.instances.query_vnflcm_occ_id(self.vnf_lcm_op_occ_id)
            .json()
            .get(OperationFields.OPERATION)
        )
        assert operation_type == OperationTypes.CHANGE_VNFPKG, log_exception(
            f"Received operation type is not {OperationTypes.CHANGE_VNFPKG}"
        )

        logger.info(f"Query {operation} CNF instance with id {self.cnf_id}")
        cnf_instance = self.api.instances.get_instance_by_id(self.cnf_id).json()
        assert cnf_instance, log_exception(
            f"Failed to get cnf instance with id {self.cnf_id!r}"
        )

        logger.info(f"Show current instantiate state of {operation} CNF instance")
        instantiation_state = cnf_instance[InstanceFields.INSTANTIATION_STATE]
        assert instantiation_state == InstantiateStates.INSTANTIATED, log_exception(
            f"Instantiate state is not {InstantiateStates.INSTANTIATED!r}"
        )

        logger.info(
            "Show CNF Instance details have been updated to match the new package"
        )
        package_id = self.api.packages_client.check_if_package_with_vnfd_id_exists(
            descriptor_id
        )

        package_vnf_data = self.api.packages.get_package_by_id(package_id).json()
        assert cnf_instance.get(
            InstantiateFields.VNF_SOFTWARE_VERSION
        ) == package_vnf_data.get(
            InstantiateFields.VNF_SOFTWARE_VERSION
        ), log_exception(
            "The VNF Software Version does not match!"
        )

        assert cnf_instance.get(InstantiateFields.VNFD_VERSION) == package_vnf_data.get(
            InstantiateFields.VNFD_VERSION
        ), log_exception("The VNF Version does not match!")

        logger.info(
            f"Verify VNF Package ID of the CNF Instance matches with the ID used in the {operation} Request"
        )
        assert cnf_instance.get(InstantiateFields.VNFD_ID) == package_vnf_data.get(
            InstantiateFields.VNFD_ID
        ), log_exception("The VNF Package ID does not match!")

    def make_scale_cnf_operation(
        self, scale_operation: str, aspect_id: str, is_additional_params: bool = False
    ) -> int:
        """
        Method to make Scale in or Scale Out operations
        :param scale_operation: operation that performed: Scale In or Scale Out
        :param aspect_id: aspect id that used for scaling
        :param is_additional_params: Flag that define usage of additional params
        :raises AssetNotFoundException: if provided operation is unknown
        """
        logger.info(f"Make {scale_operation} operation")
        start_scale_status = self.api.instances_client.get_scale_value(
            self.cnf_id, aspect_id
        )

        logger.info(f"{scale_operation} cnf instance with id {self.cnf_id!r}")
        payload = self.evnfm_test_data.instance_test_data.scale_vnf(
            scale_operation=scale_operation, aspect_id=aspect_id
        )
        payload = self.update_payload_with_lcm_operation_timeout(payload)
        payload = self.update_payload_with_additional_pars(
            payload,
            operation=EvnfmOperations.SCALE,
            package_id=self.cnf_smallstack_pkg.package_id,
            is_additional_params=is_additional_params,
        )
        logger.info(f"Scale a CNF with id={self.cnf_id}")
        response = self.api.instances.scale_vnf_instance(self.cnf_id, payload)
        self.vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)

        return start_scale_status

    def verify_scale_operation_workflow(
        self, scale_operation: Operations, aspect_id: str, start_scale_status: int
    ) -> None:
        """
        Method to verify base operation steps for Scale In or Scale Out operations

        Args:
            scale_operation: operation that performed: Scale In or Scale Out
            aspect_id: aspect id for which scale operation was done
            start_scale_status: start aspect value before scaling
        """
        logger.info(f"Verify scale workflow operations after {scale_operation}")
        self.verify_scale_operation(
            self.cnf_id, scale_operation, aspect_id, start_scale_status
        )

    def generate_payload_for_enm_node(self):
        """
        Generate payload for ENM request
        :return: Generated payload
        :rtype: dict
        """
        logger.info("Generate data for ENM request")
        payload = self.evnfm_test_data.instance_test_data.add_node_to_enm()
        payload = self.update_payload_with_lcm_operation_timeout(payload)
        return payload

    def update_payload_with_lcm_operation_timeout(self, payload):
        """
        Add cnf_lcm_operation_timeout if it present to provided payload
        :param payload: Payload that need to be changed
        :type payload: dict
        :return: Changed payload
        :rtype: dict
        """
        if self.cnf_smallstack_pkg.lcm_timeout:
            logger.debug(
                f"Update application timeout provided by user is {self.cnf_smallstack_pkg.lcm_timeout}"
            )
            timeout = {
                CommonFields.APPLICATION_TIME_OUT: self.cnf_smallstack_pkg.lcm_timeout
            }
            payload.update(timeout)
        return payload

    def modify_cnf(self, instance_id, data):
        """
        Method to modify CNF instance
        :param instance_id: instance ID
        :type instance_id: str
        :param data: instance ID
        :type data: dict
        :return: modified cnf info
        :rtype: dict
        """
        response = self.api.instances.modify_cnf_instance(data, instance_id)
        vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)
        self.api.instances_client.wait_for_lcm_operation(vnf_lcm_op_occ_id)
        return data

    def get_package_id_by_vnfd(self, vnfd_id: str) -> str:
        """
        Method that searching on CVNFM package that has provided vnfd_id
        """
        logger.info(f"Getting package id by {vnfd_id=}")
        cvnfm_pkgs = self.api.packages.get_packages().json()
        for pkg in cvnfm_pkgs:
            if pkg.get(InstantiateFields.VNFD_ID) == vnfd_id:
                return pkg.get(ApiKeys.ID)
        raise ValueError(f"No onboarded packages with {vnfd_id=}")

    def get_vnf_pkg_id_by_vnfd_id(self, vnfd_id: str) -> str | None:
        """
        Searches value of the instance vnfPkgId parameter by its vnfd_id
        Args:
            vnfd_id: vnfd_id of package. Also known as the descriptor_id
        Returns:
            vnfPkgId value
        """
        logger.info(
            f"Searching for vnfPkgId parameter value by its vnfd_id {vnfd_id!r}"
        )
        instances = self.api.instances_client.get_instances_by_vnfd(vnfd_id)
        if instances:
            # this method currently expects only one instance deployed fom a package
            # nevertheless multiple instances are possible. Will be updated in scope of EO-175598
            return instances.pop()[InstantiateFields.VNF_PKG_ID]
        logger.info(f"No VNF package with vnfd_id {vnfd_id!r} has been found")
        return None

    def get_package_cnfd_id(self, vnfd_id: str, is_unique: bool = False) -> str:
        """
        Method to get CNFD_ID from onboarded package
        Args:
            vnfd_id: vnfd_id of package. Also known as the descriptor_id
            is_unique: flag to verify whether only one instance has the specified vnfd_id
        Raises:
            UnexpectedNumberOfCnfInstances: if more than one CNF instance exists when is_unique set True
            IndexError: if no CNF instances with the specified vnfd_id found
        Returns:
            CNF package ID
        """
        logger.info(f"Getting instance id by {vnfd_id=}")
        try:
            cnf_instances = self.api.instances_client.get_instances_by_vnfd(vnfd_id)
            if is_unique and len(cnf_instances) > 1:
                raise UnexpectedNumberOfCnfInstances(
                    f"More than 1 instance with {vnfd_id=} exists: {cnf_instances}"
                )
            return cnf_instances[0].get(ApiKeys.ID)
        except IndexError as e:
            raise IndexError(f"No instance with {vnfd_id=}") from e
