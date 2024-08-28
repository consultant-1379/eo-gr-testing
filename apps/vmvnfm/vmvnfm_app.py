""" Module with VmvnfmApp class"""
import ast
import re
import uuid
from datetime import datetime
from functools import cached_property
from typing import Any

from core_libs.common.console_commands import CMD
from core_libs.common.constants import (
    ArtefactConfigKeys,
    CcdConfigKeys,
)
from core_libs.common.custom_exceptions import (
    AssetNotFoundException,
    UnexpectedInstanceState,
)
from core_libs.eo.ccd.k8s_api_client import K8sApiClient
from core_libs.eo.constants import ApiKeys
from core_libs.eo.evnfm.evnfm_constants import Operations
from core_libs.eo.vmvnfm.vmvnfm_cli import VmVnfmCli
from core_libs.eo.vmvnfm.vmvnfm_test_data import VmVnfmTestData

from apps.evnfm.data.constants import DEFAULT_EVNFM_APP_TIMEOUT
from apps.evnfm.evnfm_app import EvnfmApp
from apps.vmvnfm.data.constants import VmvnfmPaths
from apps.vmvnfm.data.service_data import VmvnfmServiceLabel, VmvnfmServiceNames
from apps.vmvnfm.data.service_model import VmvnfmServiceModel
from apps.vmvnfm.data.services import ECM_SERVICES, VIM_SERVICE
from apps.vmvnfm.data.vmvnfm_artefact_model import VmvnfmArtefactModel
from apps.vmvnfm.workflow_service import WorkflowService
from libs.common.config_reader import ConfigReader
from libs.common.vmvnfm_logging.vmvnfm_logger_setter import VmvnfmLogLevelSetter
from libs.utils.logging.logger import log_exception, logger


class VmvnfmApp(EvnfmApp):
    """
    VmvnfmApp class contains all methods related to VMVNFM and then used as test steps
    """

    def __init__(self, config: ConfigReader):
        super().__init__(config)
        self.config = config
        self.k8s_client = K8sApiClient(
            namespace=self.config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE),
            kubeconfig_path=self.config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH),
        )
        self.cli = VmVnfmCli(k8s_client=self.k8s_client)
        self.workflow_service = WorkflowService(config, vnvnfm_cli=self.cli)
        self.scale_parameters = {}
        self.log_level_setter = VmvnfmLogLevelSetter(k8s_client=self.k8s_client)

    @cached_property
    def vnf_package(self) -> VmvnfmArtefactModel:
        """
        Retrieves VNF package data from the artefact configuration file
        :raises ConfigurationNotFoundException: in case the vnf_package parameter is not found
        :return: the vnf_package configuration
        """
        return self.config.artefacts.get_by_id(ArtefactConfigKeys.VNF_TEST_PACKAGE)

    @staticmethod
    def get_tenancy_details(tenant_name: str) -> list:
        """
        Method that returns tenancy details based on given tenant name
        Args:
            tenant_name: Tenant name

        Returns:
            Tenancy details based on given tenant name
        """
        return VmVnfmTestData.create_tenancydetails_data(tenant_name, str(uuid.uuid4()))

    def get_service_template(self, service):
        """
        Loads service template JSON to the memory and deserializes it into Python dict
        :param service: a service object
        :type service: VmvnfmServiceModel
        :return: Deserialized JSON into Python dict
        :rtype: dict
        """
        logger.info("Obtaining registration template file")
        template_config_path = (
            f"{VmVnfmTestData.VMVNFM_TEMPLATE_FOLDER}/{service.template}"
        )
        json_text = self.cli.get_file_content(template_config_path)
        template_config = ast.literal_eval(json_text)
        assert isinstance(template_config, dict), log_exception(
            f"parsing {service.template} as dict failed"
        )
        return template_config

    def create_reg_file(self, service, template, registration_data):
        """
        Creates a service registration file inside the vmvnfm service pod under template folder
        :param service: a service object
        :type service: VmvnfmServiceModel
        :param template: a service template
        :type template: dict
        :param registration_data: a registration data
        :type registration_data: dict
        :return: a path to a registration file
        :rtype: str
        """
        logger.info("Creating registration file")
        if service.name == VmvnfmServiceNames.VIM:
            template["vims"][0].update(registration_data)
        else:
            template.update(registration_data)
        # remove empty keys from config:
        reg_config = {k: v for k, v in template.items() if v}
        config_filename = service.name + "_config.json"
        template_config_path = (
            f"{VmVnfmTestData.VMVNFM_TEMPLATE_FOLDER}/{config_filename}"
        )
        self.cli.write_file_by_path(reg_config, template_config_path)
        service.config_path = template_config_path
        return template_config_path

    def add_service(self, service, config_path):
        """
        Adds a service to VMVNFM
        :param service: a service object
        :type service: VmvnfmServiceModel
        :param config_path: a path to a registration file
        :type config_path: str
        """
        logger.info(f"Adding {service.name.upper()} service with the registration file")
        output_cmd = self.cli.add_service(service.name, config_path)
        assert service.add_success_text in output_cmd, log_exception(
            f"{service.name.upper()} addition failed"
        )

    def register_service(self, service, reg_data):
        """
        Registers service in VM VNFM with the given data
        :param service: the service to be registered
        :type service: VmvnfmServiceModel
        :param reg_data: a registration data
        :type reg_data: dict
        """
        template = self.get_service_template(service)
        config_path = self.create_reg_file(service, template, reg_data)
        self.add_service(service, config_path)

    def get_service_list(self, service: str | VmvnfmServiceModel) -> str:
        """
        Returns cmd output with registered services list
        Args:
            service: the service to be checked
        Returns:
            cmd output
        """
        if isinstance(service, VmvnfmServiceModel):
            service = service.name
        logger.info(f"Searching for the {service}")
        return self.cli.list_services(service_name=service)

    def get_vnf_id(self, vapp_name: str) -> str:
        """
        Retrieving onboarded VNF package ID of the firs VNF in the table
        Args:
            vapp_name: the name of the VAPP
        Returns:
            ID of the VNF package
        Raises:
            AssetNotFoundException if no VNF found
        """
        vnf_list = self.get_service_list(VmvnfmServiceNames.VNF)
        regex = r"\s{1,}\d{1,}\s{1,}\|\s(?P<vnf_id>.{36}).*" + vapp_name
        try:
            return re.search(regex, vnf_list).groupdict()["vnf_id"]
        except AttributeError:
            raise AssetNotFoundException(
                log_exception("No VNF IDs found on the VM VNFM VNFLCM pod")
            ) from None

    def get_vim_service_by_name(self, service_instance_name):
        """
        Returns cmd output with registered services list
        :param service_instance_name: the name of the service instance
        :type service_instance_name: str
        :return: cmd output
        :rtype: str
        """
        logger.info(f"Searching for the VIM: {service_instance_name}")
        return self.cli.get_vim_service_instance(service_instance_name)

    def get_registered_vim_name(self, vim_regex: str | None = None) -> str:
        """
        Obtains the name of the registered VIM zone
        Args:
            vim_regex: A regular expression for matching the VIM name
        Returns:
            VIM zone name %Y-%m-%dT%H-%M-%S
        """
        vim_regex = (
            vim_regex or r"vim_eogr_[\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}-[\d]{2}-[\d]{2}"
        )
        logger.info(f"Searching for the VIM with {vim_regex=}")
        cmd_output = self.get_service_list(VIM_SERVICE)
        r = re.search(vim_regex, cmd_output)
        return r.group()

    def get_latest_vnf_instance(self) -> dict:
        """
        Obtains the name of the latest VNF instance
        Returns:
            A dict with the VNF instance data
        """
        logger.info(f"Getting the latest VNF instance")
        return self.api.instances.get_instances().json().pop()

    @staticmethod
    def service_exists(service, output_cmd):
        """
        Checks if a service exists in VMVNFM
        :param service: the service to be checked
        :type service: VmvnfmServiceModel
        :param output_cmd: the output cmd from get service(s)
        :type output_cmd: str
        :return: True or False
        :rtype: bool
        """
        logger.info(f"Checking if service {service.name} exists")
        return not any(
            msg in output_cmd
            for msg in [service.not_found_text, service.alternative_not_found_text]
        )

    def _delete_service(self, service: VmvnfmServiceModel, cmd: str) -> None:
        """
        Deletes a service
        Args:
            service: the service to be deleted
            cmd: a command for service deletion
        Raises:
            AssertionError: when service deleting failed
        """
        logger.info(f"Deleting {service.name} service")
        output_cmd = self.cli.execute_vnflcm_cli_command(cmd)
        assert service.delete_success_text in output_cmd, log_exception(
            f"{service.name.upper()} service delete failed"
        )

    def _delete_duplicated_services(
        self, service: VmvnfmServiceModel, cmd: str
    ) -> None:
        """
        Deletes duplicated services using the index
        Args:
            service: the service to be deleted
            cmd: command for service deletion with its arguments as a separate list items
        """
        logger.info(f"Deleting {service.name} service")
        self.cli.execute_vnflcm_interactive_cli_command(cmd=cmd, intended_answer="1")

    def delete_service_config(self, file_path):
        """
        Deleting files by its path
        :param file_path: Linux path to the file
        :type file_path: str
        """
        logger.info(f"Deleting service config file {file_path}")
        self.cli.remove_file_from_pod(file_path)

    def delete_service_by_name(self, service_instance_name, service):
        """
        Deletes service by name from VM VNFM
        :param service_instance_name: the name of the service instance
        :type service_instance_name: str
        :param service: the service to be deleted
        :type service: VmvnfmServiceModel object
        """
        logger.info(f"Delete the service by name {service_instance_name} from VM VNFM")
        delete_cmd = VmVnfmTestData.DELETE_BY_NAME.format(
            service.name, service_instance_name
        )
        self._delete_service(service, delete_cmd)

    def delete_service_by_baseurl(self, base_url, service):
        """
        Deletes service by base URL from VM VNFM
        :param base_url: the base URL of the service to be deleted
        :type base_url: str
        :param service: the service to be deleted
        :type service: VmvnfmServiceModel
        """
        logger.info(f"Delete the service by base URL {base_url} from VM VNFM")
        num_of_registered_services = self._count_services_with_given_param(
            param=base_url, service=service
        )
        if num_of_registered_services:
            delete_command = VmVnfmTestData.DELETE_COMMAND.format(
                service.name, base_url
            )
            while num_of_registered_services:
                if num_of_registered_services > 1:
                    # if more than one service, it can be deleted with interactive command
                    self._delete_duplicated_services(service, delete_command)
                else:
                    # single service can be deleted without interactive command
                    self._delete_service(service, delete_command)
                # check the remaining amount of service instances
                num_of_registered_services = self._count_services_with_given_param(
                    base_url, service=service
                )
            assert not self.service_exists(
                service, self.cli.list_services(service.name)
            ), log_exception(f"{service.name.upper()} service delete failed")
        else:
            logger.info(
                f"{service.name} with the given baseUrl: {base_url} is not found"
            )

    def _count_services_with_given_param(
        self, param: str, service: VmvnfmServiceModel
    ) -> int:
        """
        Counts the number of register service instances with a given baseUrl
        Args:
            param: base URL, subscribe id or any other to search for
            service: the service to be counted
        Returns:
            the number of service instances found registered with the given baseUrl
        """
        logger.info(
            f"Searching for the {service.name} with the given parameter: {param}"
        )
        output_cmd = self.cli.list_services(service_name=service.name)
        no_alternative = service.alternative_not_found_text in output_cmd
        assert (
            service.not_found_text in output_cmd
            or no_alternative
            or output_cmd.count("baseUrl") > 0
        ), log_exception(
            f"{service.name} list output is invalid, "
            "check the 'eric-vnflcm-service-0' POD health!"
        )
        return output_cmd.count(param)

    def cleanup_ecm_services(self, base_url):
        """
        Deletes service by baseurl as well as its configuration file created on registration step
        if service doesn't have 'pre-registered' label.
        :param base_url: the base url
        :type base_url: str
        """
        for service in ECM_SERVICES:
            if VmvnfmServiceLabel.PRE_REGISTERED not in service.labels:
                self.delete_service_by_baseurl(base_url, service)
                self.delete_service_config(service.config_path)

    def cleanup_vim_service(self, vim_name):
        """
        Delete VIM service by name as well as its configuration file created on registration step
        :param vim_name: the name of current VIM instance
        :type vim_name: str
        """
        self.delete_service_by_name(vim_name, VIM_SERVICE)
        self.delete_service_config(VIM_SERVICE.config_path)

    def install_vnf_package(self, package_url, vnfd_id):
        """
        Attempts to install a VNF package into VMVNFM
        :param vnfd_id: the vnfd id of the package to be installed
        :type vnfd_id: str
        :param package_url: the url of the package where it should be downloaded from
        :type package_url: str
        """
        logger.info("Installing VNF package...")
        timebased_id = datetime.now().strftime("%y_%m_%d_%H_%M_%S")
        temp_dir = f"/tmp/{timebased_id}"

        logger.info(
            f"Creating temporary dir to store the downloaded package: {temp_dir}"
        )
        cmd = CMD.MK_DIR.format(temp_dir)
        self.cli.execute_vnflcm_cli_command(cmd)

        logger.info("Downloading package from repository...")
        self.cli.download_file_to_pod(package_url, temp_dir)
        cmd = CMD.FIND_FILE.format(temp_dir)
        downloaded_package_filepath = self.cli.execute_vnflcm_cli_command(cmd).strip()

        package_dir = f"{VmvnfmPaths.PACKAGES_REPO}{vnfd_id}"
        logger.info(
            f"Creating package dir based on the vnfd_id of the package: {package_dir}"
        )
        cmd = CMD.MK_DIR.format(package_dir)
        self.cli.execute_vnflcm_cli_command(cmd)

        logger.info(f"Unzipping downloaded file into package dir: {package_dir}")
        cmd = CMD.UNZIP_TO_DIR.format(downloaded_package_filepath, package_dir)
        self.cli.execute_vnflcm_cli_command(cmd)

        logger.info(f"Deleting downloaded package file: {downloaded_package_filepath}")
        self.cli.remove_file_from_pod(downloaded_package_filepath)

    def uninstall_vnf_package(self, vnfd_id):
        """
        Attempts to delete a VNF package from VMVNFM
        :param vnfd_id: the vnfd id of the package to be removed
        :type vnfd_id: str
        """
        logger.info("Uninstalling VNF package from VM VNFM...")
        package_dir = f"{VmvnfmPaths.PACKAGES_REPO}{vnfd_id}"
        logger.info(
            f"Recursively deleting the content of the package dir: {package_dir}"
        )
        cmd = CMD.RM_R.format(package_dir)
        self.cli.execute_vnflcm_cli_command(cmd)

    def delete_registered_ecm_services_by_url(self, base_url):
        """
        Checks if ECM services with specified base url are already registered.
        If yes deletes them and labels as pre-registered so they not to be deleted after test.
        :param base_url: the base url
        :type base_url: str
        """
        for service in ECM_SERVICES:
            if self.is_service_registered(base_url, service):
                self.delete_service_by_baseurl(base_url, service)
                self.delete_service_config(service.config_path)
                service.labels.append(VmvnfmServiceLabel.PRE_REGISTERED)

    def is_service_registered(self, base_url: str, service: VmvnfmServiceModel) -> bool:
        """
        Checks if ECM services with specified base url is registered.

        Args:
            base_url: the base url
            service: Vmvnfm service that should be checked
        Returns:
            True if service registered else False
        """
        return self._count_services_with_given_param(base_url, service) > 0

    def update_package_environment_file(self, vnfd_id: str, **kwargs: Any) -> None:
        """
        This method is updated package's environment file for VMVNFM Scale operations.
        It's workaround for https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/SM-105912,
        and might be removed after fixing.

        Args:
            vnfd_id: the vnfd id of the package to be installed
            **kwargs: keyword arguments.
                Keyword arguments:
                    vn_vim_zone_id: VN VIM zone id
                    image_name: name of package's image
                    srt_vim_name: SRT name on VIM zone
                    external_subnet_gateway: external subnet gateway
                    external_ip_for_mgmnt_node_oam: external ip for services
                    cidr: VN name
        Raises:
            AssetNotFoundException: when Environment File is not found
        """
        logger.info(f"Start preparing Environment File for package with {vnfd_id=}")
        # we generate scale_parameters for both SCALE OUT and SCALE IN operations,
        # SCALE IN is not possible without previously SCALE OUT
        self.scale_parameters = (
            self.cli.vmvnfm_test_data.compose_package_scale_parameters(**kwargs)
        )

        env_files_path = VmvnfmPaths.ENVIRONMENT_FILES.format(descriptor_id=vnfd_id)

        logger.info("Get Environment File name")
        cmd = CMD.LS.format(env_files_path)
        env_file_name = self.cli.execute_vnflcm_cli_command(cmd).strip()

        if not env_file_name:
            raise AssetNotFoundException("Environment File is not found")

        env_file_path = env_files_path + env_file_name

        logger.info(f"Update Environment File: {env_file_name} with new data")
        self.cli.write_file_by_path(self.scale_parameters, env_file_path)
        logger.info(f"Environment File {env_file_name} is successfully updated")

    def make_scale_vnf_operation(
        self, instance_id: str, scale_operation: Operations, aspect_id: str
    ) -> int:
        """
        Method for scale VMVNFM instance
        Args:
            instance_id: id of VMVNFM instance
            scale_operation: operation that performed: either 'Scale In' or 'Scale Out'
            aspect_id: aspect id that used for scaling (VM id in EOCM)
        Raises:
            ValueError: for incorrect scale_operation

        Returns:
            Initial value of scale level
        """
        init_scale_level = self.api.instances_client.get_scale_value(
            instance_id, aspect_id
        )
        logger.info(
            f"Start '{scale_operation}' operation for {aspect_id=} in VNF {instance_id=}..."
        )

        if Operations.SCALE_IN == scale_operation:
            # we use additional params in payload for SCALE IN operation,
            # while for SCALE OUT we replace packages env file
            additional_params = self.scale_parameters["parameters"]
        else:
            additional_params = None

        response = self.api.instances.scale_vnf_instance(
            instance_id=instance_id,
            payload=self.evnfm_test_data.instance_test_data.scale_vnf(
                scale_operation=scale_operation,
                aspect_id=aspect_id,
                additional_params=additional_params,
            ),
        )
        self.vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)

        return init_scale_level

    def make_and_verify_scale_operation(
        self, instance_id: str, scale_operation: Operations, aspect_id: str
    ) -> None:
        """
        Make and verify Scale operation on VMVNFM instance
        Args:
            instance_id: id of VMVNFM instance
            scale_operation: operation that performed: either 'Scale In' or 'Scale Out'
            aspect_id: aspect id that used for scaling (VM id in EOCM)
        """
        init_scale_level = self.make_scale_vnf_operation(
            instance_id, scale_operation, aspect_id
        )
        self.verify_scale_operation(
            instance_id=instance_id,
            scale_operation=scale_operation,
            aspect_id=aspect_id,
            start_scale_status=init_scale_level,
        )

    def make_and_verify_heal_operation(self, vnf_id: str) -> None:
        """
        Performs VNF heal operation and verifies its result
        Args:
            vnf_id: an ID of the VNF to be healed
        """
        logger.info(f"Triggering heal operation for {vnf_id=}")
        payload = {"cause": "VNF_healing"}
        response = self.api.instances_client.heal_vnf_instance(vnf_id, payload)
        self.vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)

        self.verify_heal_operation()

    def create_vnf_instance_identifier(
        self,
        descriptor_id: str,
        vnf_pkg_id: str,
        is_ve_vnfm: bool = False,
        vapp_name: str | None = None,
    ) -> str:
        """
        Create VNF Instance identifier for onboarded CNF package
        Args:
            descriptor_id: VNFD ID
            vnf_pkg_id: ID of the VNF package
            is_ve_vnfm: flag to choose the API endpoint either Or-VNFM or Ve-VNFM
            vapp_name: the VAPP name
        Returns:
            VNF Instance ID
        """
        logger.info(f"Create VNF Instance identifier")
        create_identifier_json = (
            self.evnfm_test_data.instance_test_data.create_vnf_identifier_data(
                descriptor_id, vnf_pkg_id, vapp_name
            )
        )

        vnf_id = self.api.instances.create_instance_identifier(
            create_identifier_json, is_ve_vnfm=is_ve_vnfm
        ).json()[ApiKeys.ID]
        return vnf_id

    def get_vnf_deployment_data(self, **kwargs):
        """
        Generates data required for the VNF instantiation operation
        Args:
            **kwargs: keyword parameters as follows:
                Mandatory:
                 - vn_vim_obj_id (str): Virtual Network VIM object ID - ID of
                 the VN on the VIM zone side
                 - srt_vim_name (str): SRT VIM object name
                 - vim_name (str): VIM zone name that is registered in EO CM and VM VNFM
        Returns:
            Data for the VNF deployment request
        """
        return self.evnfm_test_data.instance_test_data.get_vnf_instantiation_data(
            **kwargs
        )

    def instantiate_vnf(
        self,
        vnf_id: str,
        vn_vim_obj_id: str,
        srt_vim_name: str,
        vim_name: str,
        **kwargs,
    ) -> str:
        """
        Deploys VNF package
        Args:
            vnf_id: ID of the VNF in
            vn_vim_obj_id: Virtual Network VIM object ID - ID of the VN on the VIM zone side
            srt_vim_name: SRT VIM object name
            vim_name: VIM zone name
            kwargs: keyword parameters
        Returns:
            ID of the instantiated package
        Raises:
            UnexpectedInstanceState: in case during deploying some errors happen
        """
        logger.info("Instantiate VNF package")
        instantiate_data = self.get_vnf_deployment_data(
            vn_vim_obj_id=vn_vim_obj_id,
            srt_vim_name=srt_vim_name,
            vim_name=vim_name,
            **kwargs,
        )

        logger.info(f"Sending Instantiate VNF request for CNF ID {vnf_id}")
        response = self.api.instances.instantiate_cnf(vnf_id, instantiate_data)
        vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)

        logger.info(
            f"Verifying VNF Lifecycle operation state for vnfLcmOpOccId {vnf_lcm_op_occ_id}"
        )
        try:
            #  A workaround for the problem described in SM-163009.
            #  When the issue is resolved please remove the workaround
            #  by uncommenting the following line and deleting the line that follows it:
            #  self.api.instances_client.wait_for_lcm_operation(vnf_lcm_op_occ_id)
            self.api.instances_client.wait_for_lcm_operation(
                vnf_lcm_op_occ_id, check_response=False
            )
        except UnexpectedInstanceState as exception:
            cleanup_json = (
                self.evnfm_test_data.instance_test_data.cleanup_instance_json()
            )
            self.api.instances.clean_up_failed_instance(vnf_id, cleanup_json)
            self.api.instances_client.wait_for_cnf_deletion(vnf_id)
            raise UnexpectedInstanceState(
                f"Unexpected instance state during instantiation. Instance id: {vnf_id}"
            ) from exception
        #  A workaround for the problem described in SM-163009.
        #  When the issue is resolved please remove the workaround
        #  by uncommenting the following line and deleting the line that follows it:
        #  self.is_package_instantiated(vnf_id)
        self.is_package_instantiated(vnf_id, check_response=False)
        return vnf_id

    def terminate_instance(
        self, instance_id: str, remove_package_id: bool = True
    ) -> None:
        """
        Terminates VNF instance
        Args:
            instance_id: VNF instance ID
            remove_package_id: Flag which defines whether to remove VNF package ID form the VM VNFM
        """
        logger.info("Terminate VNF instance")
        terminate_payload = (
            self.evnfm_test_data.instance_test_data.delete_cnf_instance_json(
                application_time_out=DEFAULT_EVNFM_APP_TIMEOUT
            )
        )
        response = self.api.instances.delete_cnf(instance_id, terminate_payload)
        vnf_lcm_op_occ_id = self.get_vnf_lcm_op_occ_id_from_response(response)
        self.api.instances_client.wait_for_lcm_operation(vnf_lcm_op_occ_id)

        if remove_package_id:
            self.api.instances.delete_instance_identifier(instance_id)

    def set_debug_log_level(self) -> None:
        """
        Method for setting DEBUG logging level for VMVNFM services
        """
        self.log_level_setter.set_log_level()
