"""
This module contains a test functions to execute first Phase A of GR testing
"""
from pytest import fixture, mark

from apps.cvnfm.cluster import Cluster
from apps.cvnfm.cvnfm_app import CvnfmApp
from libs.utils.logging.logger import log_exception

# pylint: disable=unused-argument

pytestmark = [mark.cvnfm, mark.cvnfm_phase_A]


@fixture(scope="module", autouse=True)
def download_cvnfm_pkg(download_cvnfm_instantiate_pkg: None) -> None:
    """
    Download CVNFM package on file system
    Args:
        download_cvnfm_instantiate_pkg: fixture that download Instantiate CVNFM package
                                        on the file system
    """


def test_register_default_cluster(
    cluster_app: Cluster, register_cluster_and_clean_up: str
) -> None:
    """
    Function verify that cluster can successfully register
    """
    assert cluster_app.is_cluster_config_registered(), log_exception(
        "Cluster config not registered"
    )


def test_onboard_package(cvnfm_app: CvnfmApp, onboard_cnf_package: callable):
    """
    Function verify next workflow:
    1. Onboard CVNFM package
    2. Delete package form CVNFM
    3. Onboard again CVNFM package
    """
    onboard_cnf_package(cvnfm_app.cnf_smallstack_pkg)
    cvnfm_app.delete_cnf_package_if_exists(cvnfm_app.cnf_smallstack_pkg.descriptor_id)
    onboard_cnf_package(cvnfm_app.cnf_smallstack_pkg)


def test_instantiate_package(cvnfm_app: CvnfmApp, instantiate_cnf_package: callable):
    """
    Function verify next workflow:
    1. Instantiate CVNFM package
    2. Terminate CVNFM instance
    3. Instantiate CVNFM package
    """
    instantiate_cnf_package(cvnfm_app.cnf_smallstack_pkg)
    cvnfm_app.terminate_cnf_instance(cvnfm_app.cnf_id)
    instantiate_cnf_package(cvnfm_app.cnf_smallstack_pkg)
