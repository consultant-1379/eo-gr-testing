"""
This module contains a test functions to execute second Phase B of GR testing
"""

from core_libs.eo.evnfm.evnfm_constants import Operations
from pytest import fixture
from pytest import mark

from apps.cvnfm.cvnfm_app import CvnfmApp
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import logger

# pylint: disable=unused-argument

pytestmark = [mark.cvnfm]


@fixture(scope="module", autouse=True)
def setup_preconditions(cvnfm_app: CvnfmApp) -> None:
    """
    Get package id and instance id from Phase A
    Download CVNFM upgrade package on file system
    """
    logger.info("Getting package id and instance id from Phase A")
    cvnfm_app.cnf_smallstack_pkg.package_id = cvnfm_app.get_package_id_by_vnfd(
        cvnfm_app.cnf_smallstack_pkg.descriptor_id
    )
    cvnfm_app.cnf_id = cvnfm_app.get_package_cnfd_id(
        cvnfm_app.cnf_smallstack_pkg.descriptor_id, is_unique=True
    )

    logger.info("Download upgrade CNF package")
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_upgrade_smallstack_pkg,
        is_randomize_vnfd=ENV_VARS.is_randomize_vnfd,
    )


@mark.cvnfm_phase_B
@mark.cvnfm_phase_C
def test_onboard_upgrade_package(cvnfm_app: CvnfmApp, onboard_cnf_package: callable):
    """
    Function verify next workflow:
    1. Onboard CVNFM upgrade package
    2. Delete package upgrade from CVNFM
    3. Onboard again CVNFM package
    """
    onboard_cnf_package(cvnfm_app.cnf_upgrade_smallstack_pkg)
    cvnfm_app.delete_cnf_package_if_exists(
        cvnfm_app.cnf_upgrade_smallstack_pkg.descriptor_id
    )
    onboard_cnf_package(cvnfm_app.cnf_upgrade_smallstack_pkg)


@mark.cvnfm_phase_B
@mark.cvnfm_phase_C
def test_upgrade_and_terminate_package(cvnfm_app: CvnfmApp):
    """
    Function verify next workflow:
    1. Upgrade CVNFM package with CNF Upgrade package
    2. Terminate CVNFM instance
    3. Delete CVNF package
    """
    cnf_package_id = cvnfm_app.get_vnf_pkg_id_by_vnfd_id(
        cvnfm_app.cnf_smallstack_pkg.descriptor_id
    )
    cvnfm_app.upgrade_vnf_instance(
        ENV_VARS.is_additional_params_for_change_pkg,
        cnf_package_id,
    )
    cvnfm_app.verify_instance_workflow_operations(operation=Operations.UPGRADE)
    cvnfm_app.terminate_cnf_instance(cvnfm_app.cnf_id)
    cvnfm_app.delete_cnf_package_if_exists(
        cvnfm_app.cnf_upgrade_smallstack_pkg.descriptor_id
    )


@mark.cvnfm_phase_B
@mark.cvnfm_phase_C
def test_instantiate_package(cvnfm_app: CvnfmApp, instantiate_cnf_package: callable):
    """
    Function verify next workflow:
    1. Instantiate CVNFM package for instantiate
    """
    instantiate_cnf_package(cvnfm_app.cnf_smallstack_pkg)


@mark.cvnfm_phase_C
def test_clean_up_instance_and_package(cvnfm_app: CvnfmApp):
    """
    Function delete package and resources but only with
    """
    if ENV_VARS.is_resources_clean_up:
        logger.info("Delete resources from CVNFM")
        cvnfm_app.terminate_cnf_instance(cvnfm_app.cnf_id)
        cvnfm_app.delete_cnf_package_if_exists(
            cvnfm_app.cnf_smallstack_pkg.descriptor_id
        )
    else:
        logger.info("Test skipped as resources clean up is not needed")
