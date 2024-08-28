"""
Module to store VM VNFM application-related pytest fixtures
"""

# pylint: disable=unused-argument
from typing import Generator, Callable

from core_libs.common.misc_utils import (
    encode_to_base64_string,
)
from core_libs.vim.openstack import OpenStack
from openstack.compute.v2.flavor import Flavor
from openstack.image.v2.image import Image
from openstack.network.v2.network import Network
from pytest import fixture

from apps.vim_app import VimApp
from apps.vmvnfm.data.services import VIM_SERVICE
from apps.vmvnfm.data.vmvnfm_artefact_model import VmvnfmArtefactModel
from apps.vmvnfm.vmvnfm_app import VmvnfmApp
from libs.common.asset_names import AssetNames
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import logger


@fixture(scope="session", autouse=True)
def set_debug_log_level_for_vmvnfm(vmvnfm_app: VmvnfmApp) -> None:
    """
    Fixture that sets DEBUG logging level for VMVNFM
    """
    if ENV_VARS.enable_vmvnfm_debug_log_level:
        vmvnfm_app.set_debug_log_level()


@fixture(scope="package")
def check_and_remove_registered_vim(
    vim_app: VimApp, vmvnfm_app: VmvnfmApp
) -> Generator:
    """
    The pytest fixture that verifies VIM registration and
    de-registers it after the test session
    Args:
        vim_app: the vim_app fixture
        vmvnfm_app: the vmvnfm_app fixture
    """
    # Delete targeted VIM (VIM to be registered by test) in case it exists.
    targeted_vim_registered = vmvnfm_app.service_exists(
        VIM_SERVICE,
        vmvnfm_app.get_vim_service_by_name(service_instance_name=vim_app.vim_name),
    )
    if targeted_vim_registered:
        vmvnfm_app.cleanup_vim_service(vim_app.vim_name)
    yield
    # If targeted VIM (VIM to be registered by test) existed before test, don't delete it after test
    # as by GAT requirements, the system should be left in that state that it was before.
    if not targeted_vim_registered and ENV_VARS.is_resources_clean_up:
        vmvnfm_app.cleanup_vim_service(vim_app.vim_name)


@fixture(scope="package")
def vim_registration(
    vim_app: VimApp, vmvnfm_app: VmvnfmApp, check_and_remove_registered_vim: Generator
) -> None:
    """
    Registering VIM in VM VNFM by adding VIM JSON configuration.
    :param vim_app: the vim_app fixture
    :param vmvnfm_app: the vmvnfm_app fixture
    :param check_and_remove_registered_vim: verifies VIM registration and
    de-registers it after the test session
    """
    cmd_output = vmvnfm_app.get_service_list(VIM_SERVICE)
    # If there is existing default VIM prepare data for registration of non-default VIM.
    if vmvnfm_app.service_exists(VIM_SERVICE, cmd_output) and "True" in cmd_output:
        registration_data = vim_app.prepare_data_for_vmvnfm_integration(
            default_vim=False
        )
    # In other cases prepare data for registration of default VIM.
    else:
        registration_data = vim_app.prepare_data_for_vmvnfm_integration()
    vmvnfm_app.register_service(VIM_SERVICE, registration_data)


@fixture(scope="session")
def workflow_setup_and_clean_up(
    vmvnfm_app: VmvnfmApp, check_and_remove_registered_workflow: Generator
) -> Generator:
    """
    The pytest fixture that download RPM Package and delete it after the test
    Args:
        vmvnfm_app: the vmvnfm_app fixture
        check_and_remove_registered_workflow: fixture that verifies Workflow registration and
                                        de-registers it after the test session
    """
    rpm_package_path = vmvnfm_app.workflow_service.download_rpm_package()
    vmvnfm_app.workflow_service.install_workflow(rpm_package_path)
    yield
    vmvnfm_app.workflow_service.remove_rpm_package(rpm_package_path)


@fixture(scope="session")
def generic_workflow_setup_and_clean_up(
    vmvnfm_app: VmvnfmApp,
    check_and_remove_registered_generic_workflow: None,
) -> Generator:
    """
    The pytest fixture that downloads Generic RPM Package and deletes it after the test
    Args:
        vmvnfm_app: the vmvnfm_app fixture
        check_and_remove_registered_generic_workflow: fixture that verifies Generic Workflow registration and
                                        de-registers it after the test session
    """
    package_path = vmvnfm_app.workflow_service.generic_workflow_package_path
    rpm_package_path = vmvnfm_app.workflow_service.download_rpm_package(package_path)
    vmvnfm_app.workflow_service.install_workflow(rpm_package_path)
    yield
    vmvnfm_app.workflow_service.remove_rpm_package(rpm_package_path)


@fixture(scope="session")
def check_and_remove_registered_workflow(vmvnfm_app: VmvnfmApp) -> Generator:
    """
    The pytest fixture that verifies Workflow registration and
    de-registers it after the test session
    Args:
        vmvnfm_app: the vmvnfm_app fixture
    """
    workflow_pre_installed = vmvnfm_app.workflow_service.is_workflow_installed()
    # Delete targeted workflow (workflow to be installed by test) in case it exists.
    if workflow_pre_installed:
        vmvnfm_app.workflow_service.uninstall_workflow()
    yield
    # If targeted workflow (workflow to be installed by test) existed before test,
    # don't delete it after test as by GAT requirements, the system should be left
    # in that state that it was before.
    if not workflow_pre_installed and ENV_VARS.is_resources_clean_up:
        vmvnfm_app.workflow_service.uninstall_workflow()


@fixture(scope="session")
def check_and_remove_registered_generic_workflow(vmvnfm_app: VmvnfmApp) -> Generator:
    """
    The pytest fixture that verifies Generic Workflow registration and
    de-registers it after the test session
    Args:
        vmvnfm_app: the vmvnfm_app fixture
    """
    workflow_path = vmvnfm_app.workflow_service.generic_workflow_package_path
    workflow_pre_installed = vmvnfm_app.workflow_service.is_workflow_installed(
        workflow_path
    )
    # Delete targeted workflow (workflow to be installed by test) in case it exists.
    if workflow_pre_installed:
        vmvnfm_app.workflow_service.uninstall_workflow(workflow_path)
    yield
    if not workflow_pre_installed and ENV_VARS.is_resources_clean_up:
        vmvnfm_app.workflow_service.uninstall_workflow(workflow_path)


@fixture(scope="session")
def install_package_in_vmvnfm_and_clean_up(
    vmvnfm_app: VmvnfmApp,
) -> Generator[Callable, None, None]:
    """
    Install package into VMVNFM (/vnflcm-ext/current/vnf_package_repo/) and then clean up
    Args:
        vmvnfm_app: VmvnfmApp instance
    Yields:
        function for install package into VMVNFM
    """
    packages = []
    try:

        def inner_func(package: VmvnfmArtefactModel) -> None:
            """
            Inner function of installing package into VMVNFM
            Args:
                package: package model from config
            """
            vmvnfm_app.install_vnf_package(package.url, package.descriptor_id)
            packages.append(package)

        yield inner_func

    finally:
        if packages and ENV_VARS.is_resources_clean_up:
            for pkg in packages:
                vmvnfm_app.uninstall_vnf_package(pkg.descriptor_id)


@fixture
def configure_assets_on_vnflcm(
    vim_registration: None,
    workflow_setup_and_clean_up: None,
    generic_workflow_setup_and_clean_up: None,
) -> None:
    """
    Configuring the following assets on the VNFLCM: VIM zone and The Workflow service
    Args:
        vim_registration: Registers VIM in the VM VNFM by adding VIM JSON configuration
        workflow_setup_and_clean_up: download RPM Package and delete it after the test
        generic_workflow_setup_and_clean_up: download Generic RPM Package and delete it after the test
    """
    logger.info("Configuring assets on the VNFLCM: VIM zone and The Workflow service")


@fixture
def create_openstack_image_and_clean_up(
    openstack_app: OpenStack,
    vmvnfm_app: VmvnfmApp,
    asset_names: AssetNames,
) -> Generator[Image, None, None]:
    """
    Creates and uploads an image to the OpenStack
    Args:
        openstack_app: fixture that initializes an OpenStack wrapper
        vmvnfm_app: fixture that creates a VmvnfmApp object
        asset_names: an AssetNames instance
    Yields:
        Uploaded Image object
    """
    package_path = vmvnfm_app.download_file(vmvnfm_app.vnf_package.url)
    image = openstack_app.images.create_image(
        name=asset_names.openstack_image_name, filename=str(package_path)
    )
    yield image
    if ENV_VARS.is_resources_clean_up:
        openstack_app.images.delete_image(image.name)


@fixture
def create_openstack_flavor_and_clean_up(
    openstack_app: OpenStack,
    asset_names: AssetNames,
) -> Generator[Flavor, None, None]:
    """
    Creates a flavor on the OpenStack
    Args:
        openstack_app: fixture that initializes an OpenStack wrapper
        asset_names: an AssetNames instance
    Yields:
        Created Flavor object
    """
    flavor = openstack_app.flavors.create_flavor(name=asset_names.openstack_flavor_name)
    yield flavor
    if ENV_VARS.is_resources_clean_up:
        openstack_app.flavors.delete_flavor(flavor.name)


@fixture
def create_openstack_network_and_clean_up(
    openstack_app: OpenStack,
    vim_app: VimApp,
    asset_names: AssetNames,
) -> Generator[Network, None, None]:
    """
    Creates a network on the OpenStack
    Args:
        openstack_app: fixture that initializes an OpenStack wrapper
        vim_app: fixture that initializes VimApp object
        asset_names: an AssetNames instance
    Yields:
        Created Network object
    """
    network = openstack_app.networks.create_network(
        name=asset_names.openstack_network_name,
        project_id=vim_app.vim_obj_id,
    )
    openstack_app.networks.create_subnet(network.id)
    yield network
    if ENV_VARS.is_resources_clean_up:
        openstack_app.networks.delete_network(network.name)


@fixture
def deploy_vnf_package_via_or_vnfm(
    vmvnfm_app: VmvnfmApp,
    configure_assets_on_vnflcm: None,
    install_package_in_vmvnfm_and_clean_up: Callable,
    create_openstack_image_and_clean_up: Image,
    create_openstack_flavor_and_clean_up: Flavor,
    create_openstack_network_and_clean_up: Network,
    vim_app: VimApp,
    asset_names: AssetNames,
) -> Generator[str, None, None]:
    """
    Deploys VNF APP
    Args:
        vmvnfm_app: VM VNFM app
        configure_assets_on_vnflcm: configures assets on the VNFLCM
        install_package_in_vmvnfm_and_clean_up: fixture that installs package into VM VNFM
        create_openstack_image_and_clean_up: fixture that creates and uploads an image to the OpenStack
        create_openstack_flavor_and_clean_up: fixture that creates a flavor on the OpenStack
        create_openstack_network_and_clean_up: fixture that creates a network on the OpenStack
        vim_app: the vim_app fixture
        asset_names: an AssetNames instance
    Yields:
        The name of the created VAPP
    """
    install_package_in_vmvnfm_and_clean_up(vmvnfm_app.vnf_package)
    image = create_openstack_image_and_clean_up
    flavor = create_openstack_flavor_and_clean_up
    network = create_openstack_network_and_clean_up
    vapp_name = asset_names.openstack_stack_vapp_name
    instance_id = None
    try:
        instance_id = vmvnfm_app.create_vnf_instance_identifier(
            vmvnfm_app.vnf_package.descriptor_id,
            image.id,
            is_ve_vnfm=False,
            vapp_name=vapp_name,
        )
        vmvnfm_app.instantiate_vnf(
            instance_id,
            network.id,
            flavor.name,
            vim_app.vim_name,
            vm_image=image.name,
            compute_node_flavor=True,
            projectId=vim_app.vim_obj_id,
            projectName=vim_app.project_name,
            password=encode_to_base64_string(vim_app.admin_password),
        )
        yield vapp_name
    finally:
        if instance_id and ENV_VARS.is_resources_clean_up:
            vmvnfm_app.terminate_instance(instance_id)


@fixture(scope="package")
def check_registered_generic_workflow(
    vmvnfm_app: VmvnfmApp,
) -> Generator:
    """
    The pytest fixture that verifies Generic Workflow registration
    Args:
        vmvnfm_app: the vmvnfm_app fixture
    """
    workflow_path = vmvnfm_app.workflow_service.generic_workflow_package_path
    workflow_pre_installed = vmvnfm_app.workflow_service.is_workflow_installed(
        workflow_path, apply_wait=True
    )
    yield workflow_pre_installed


@fixture(scope="package")
def get_registered_image(
    openstack_app: OpenStack,
    asset_names: AssetNames,
) -> Generator[Image, None, None]:
    """
    The pytest fixture that returns a registered Openstack image object
    Args:
        openstack_app: fixture that initializes an OpenStack wrapper
        asset_names: an AssetNames instance
    Yields:
        Openstack image object
    """
    image = openstack_app.images.get_image_by(asset_names.openstack_image_name)
    yield image
    if ENV_VARS.is_resources_clean_up:
        openstack_app.images.delete_image(image.id)


@fixture(scope="package")
def get_registered_flavor(
    openstack_app: OpenStack,
    get_registered_network: Network,
    asset_names: AssetNames,
) -> Generator[Flavor, None, None]:
    """
    The pytest fixture that returns a registered Openstack flavor object
    Args:
        openstack_app: a fixture that initializes an OpenStack wrapper
        get_registered_network: a fixture that returns a registered
        asset_names: an AssetNames instance
        Openstack network object
    Yields:
        Openstack flavor object
    """
    flavor = openstack_app.flavors.get_flavor_by_name_or_id(
        asset_names.openstack_flavor_name
    )
    yield flavor
    if ENV_VARS.is_resources_clean_up:
        openstack_app.flavors.delete_flavor(flavor.name)


@fixture(scope="session")
def get_registered_network(
    openstack_app: OpenStack, asset_names: AssetNames
) -> Generator[Network, None, None]:
    """
    The pytest fixture that returns a registered Openstack network object
    Args:
        openstack_app: fixture that initializes an OpenStack wrapper
        asset_names: an AssetNames instance
    Yields:
        Openstack network object
    """
    network = openstack_app.networks.get_network_details(
        asset_names.openstack_network_name
    )
    yield network
    if ENV_VARS.is_resources_clean_up:
        openstack_app.networks.delete_network(network.name)


@fixture
def deploy_vnf_package_on_registered_assets(
    vmvnfm_app: VmvnfmApp,
    install_package_in_vmvnfm_and_clean_up: Callable,
    get_registered_image: Image,
    get_registered_flavor: Flavor,
    get_registered_network: Network,
    vim_app: VimApp,
    asset_names: AssetNames,
) -> Generator[str, None, None]:
    """
    Deploys VNF APP using already registered VM VNFM and VIM zone assets
    Args:
        vmvnfm_app: VM VNFM app
        install_package_in_vmvnfm_and_clean_up: fixture that installs package into VM VNFM
        get_registered_image: fixture that returns an image uploaded to the OpenStack
        get_registered_flavor: fixture that returns a registered flavor on the OpenStack
        get_registered_network: fixture that creates a network on the OpenStack
        vim_app: the vim_app fixture
        asset_names: an AssetNames instance
    Yields:
        The name of the created VAPP
    """
    vim_app.vim_name = vmvnfm_app.get_registered_vim_name()
    install_package_in_vmvnfm_and_clean_up(vmvnfm_app.vnf_package)
    image = get_registered_image
    flavor = get_registered_flavor
    network = get_registered_network
    vapp_name = asset_names.openstack_stack_vapp_name
    instance_id = None
    try:
        instance_id = vmvnfm_app.create_vnf_instance_identifier(
            vmvnfm_app.vnf_package.descriptor_id,
            image.id,
            is_ve_vnfm=False,
            vapp_name=vapp_name,
        )
        vmvnfm_app.instantiate_vnf(
            instance_id,
            network.id,
            flavor.name,
            vim_app.vim_name,
            vm_image=image.name,
            compute_node_flavor=True,
            projectId=vim_app.vim_obj_id,
            projectName=vim_app.project_name,
            password=encode_to_base64_string(vim_app.admin_password),
        )
        yield vapp_name
    finally:
        if instance_id and ENV_VARS.is_resources_clean_up:
            vmvnfm_app.terminate_instance(instance_id)
