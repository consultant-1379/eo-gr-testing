"""
This module contains test cases that verify instantiate VNF package over VM VNFM interface
"""

# pylint: disable=unused-argument

from core_libs.eo.constants import ApiKeys
from pytest import mark

from apps.vmvnfm.vmvnfm_app import VmvnfmApp
from libs.utils.logging.logger import logger

pytestmark = [mark.vmvnfm]


@mark.vmvnfm_phase_A
def test_vnf_instantiation(deploy_vnf_package_via_or_vnfm: str):
    """
    This test case will attempt to instantiate VNF package over the VM VNFM interface.
    """
    vapp_name = deploy_vnf_package_via_or_vnfm
    logger.info(f"VAPP with {vapp_name=} is created")


@mark.vmvnfm_phase_B
@mark.vmvnfm_phase_C
def test_vnf_instantiation_check(
    vmvnfm_app: VmvnfmApp, check_registered_generic_workflow: bool
):
    """
    This test case verifies generic workflow, instantiated VNF package and terminates it
    """
    assert (
        check_registered_generic_workflow
    ), "The installed generic Workflow hasn't been found"
    vnfd_id = vmvnfm_app.vnf_package.descriptor_id

    instance = vmvnfm_app.get_ve_vnf_instance_by_vnfd_id(vnfd_id, is_unique=True)
    assert instance, f"No VNF instances with {vnfd_id=} were found"

    vmvnfm_app.terminate_instance(instance.get(ApiKeys.ID))


@mark.vmvnfm_phase_B
@mark.vmvnfm_phase_C
def test_vnf_instantiation_switchover(deploy_vnf_package_on_registered_assets: str):
    """
    This test case instantiates VNF package over the VM VNFM interface with the previously registered assets
    """
    vapp_name = deploy_vnf_package_on_registered_assets
    logger.info(f"VAPP with {vapp_name=} is created")
