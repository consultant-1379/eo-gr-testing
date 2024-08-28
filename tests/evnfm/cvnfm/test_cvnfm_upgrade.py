"""
Contains EO pre- and post-upgrade tests that instantiate and terminate a CNF package
"""
from pytest import mark

from apps.cvnfm.cluster import Cluster
from apps.cvnfm.cvnfm_app import CvnfmApp
from libs.common.env_variables import ENV_VARS
from libs.common.asset_names import AssetNames
from libs.utils.logging.logger import logger, log_exception

# pylint: disable=unused-argument

pytestmark = [mark.cvnfm]


@mark.NON_GR
@mark.cvnfm_pre_upgrade
def test_pre_upgrade_cnf_instantiation(
    cvnfm_app: CvnfmApp,
    onboard_cnf_package: callable,
    cluster_app: Cluster,
    register_cluster_and_clean_up: str,
    instantiate_cnf_package: callable,
    asset_names: AssetNames,
):
    """
    EO pre-upgrade test function
    Test steps:
    1. Register CISM cluster
    2. Onboard a signed and un-signed CNF packages
    3. Instantiate these CNF packages
    4. Onboard signed CNF upgrade package
    """
    assert cluster_app.is_cluster_config_registered(), log_exception(
        "Cluster config not registered"
    )
    logger.info("Downloading and onboarding signed CNF package")
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_smallstack_pkg, is_randomize_vnfd=ENV_VARS.is_randomize_vnfd
    )
    onboard_cnf_package(cvnfm_app.cnf_smallstack_pkg)

    logger.info("Downloading and onboarding unsigned CNF package")
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_unsigned_smallstack_pkg,
        is_randomize_vnfd=ENV_VARS.is_randomize_vnfd,
    )
    onboard_cnf_package(cvnfm_app.cnf_unsigned_smallstack_pkg)

    logger.info("Instantiating the signed and unsigned CNF packages")
    instantiate_cnf_package(cvnfm_app.cnf_smallstack_pkg)
    instantiate_cnf_package(
        cvnfm_app.cnf_unsigned_smallstack_pkg,
        instance_name=asset_names.cnf_unsigned_instance_name,
    )

    logger.info("Downloading and onboarding signed CNF upgrade package")
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_upgrade_smallstack_pkg,
        is_randomize_vnfd=ENV_VARS.is_randomize_vnfd,
    )
    onboard_cnf_package(cvnfm_app.cnf_upgrade_smallstack_pkg)


@mark.NON_GR
@mark.cvnfm_post_upgrade
def test_post_upgrade_cnf_termination(
    cvnfm_app: CvnfmApp,
    cluster_app: Cluster,
    instantiate_cnf_package: callable,
    asset_names: AssetNames,
):
    """
    EO post-upgrade test function
    Test steps:
    1. Upgrade unsigned CNF package instance to the signed one
    2. Terminate the signed CNF instance
    3. Instantiate the upgraded unsigned-to-signed package
    4. Terminate the unsigned-to-signed and the unsigned instances,
       remove onboarded CNF packages: not signed, signed and signed for upgrade,
       de-register cluster
    """
    logger.info("Upgrading unsigned CNF package instance")
    cvnfm_app.unsigned_cnf_id = cvnfm_app.api.instances_client.get_instance_id_by_name(
        name=asset_names.cnf_unsigned_instance_name
    )

    cvnfm_app.upgrade_vnf_instance(
        False,
        cvnfm_app.get_vnf_pkg_id_by_vnfd_id(
            cvnfm_app.cnf_unsigned_smallstack_pkg.descriptor_id
        ),
        cnf_id=cvnfm_app.unsigned_cnf_id,
    )

    cvnfm_app.cnf_id = cvnfm_app.api.instances_client.get_instance_id_by_name(
        name=asset_names.cnf_instance_name
    )
    logger.info("Removing CNF instances")
    cvnfm_app.terminate_cnf_instance(cvnfm_app.cnf_id)
    cvnfm_app.terminate_cnf_instance(cvnfm_app.unsigned_cnf_id)

    logger.info("Removing onboarded CNF packages")
    onboarded_packages = [
        cvnfm_app.cnf_smallstack_pkg,
        cvnfm_app.cnf_unsigned_smallstack_pkg,
        cvnfm_app.cnf_upgrade_smallstack_pkg,
    ]
    for package in onboarded_packages:
        cvnfm_app.delete_cnf_package_if_exists(package.descriptor_id)

    logger.info("Removing registered cluster")
    cluster_app.deregister_cluster_config()
