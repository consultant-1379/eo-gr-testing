"""Module to store tests that verify impact of SFTP unavailability on CVNFM packages. JIRA: OTC-14066"""

from typing import Generator

from pytest import mark, fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.cvnfm.cvnfm_app import CvnfmApp
from apps.gr.data.constants import GrBurOrchestratorDeploymentEnvVars
from apps.gr.geo_redundancy import GeoRedundancyApp
from libs.utils.logging.logger import logger


# pylint: disable=unused-argument


@fixture
def make_sftp_server_available(gr_app: GeoRedundancyApp) -> Generator:
    """
    Fixture that makes SFTP server available by scale its deployment replicas to 1 after test
    Args:
        gr_app: instance of GeoRedundancyApp
    """
    yield
    gr_app.sftp_server.change_server_replicas(replicas=1)


@fixture
def decrease_image_sync_interval_on_active_site(
    codeploy_app_active_site: CodeployApp,
) -> None:
    """
    Change default interval value for image sync on Active site
    Args:
        codeploy_app_active_site: CodeployApp instance of Active site
    """
    value = "300"
    logger.info(
        f"Changing {GrBurOrchestratorDeploymentEnvVars.IMAGE_SYNC_INTERVAL_PRIMARY} value to {value!r} "
        "on BUR Orchestrator on Active Site"
    )
    codeploy_app_active_site.update_bur_orchestrator_deployment_env_variable(
        GrBurOrchestratorDeploymentEnvVars.IMAGE_SYNC_INTERVAL_PRIMARY, value
    )


@mark.cvnfm_sftp_unavailable_before_switchover
def test_onboard_second_pkg_when_gr_sftp_unavailable(
    decrease_backup_cycle_interval_on_both_sites: None,
    decrease_image_sync_interval_on_active_site: None,
    cvnfm_app: CvnfmApp,
    onboard_cnf_package: callable,
    gr_app: GeoRedundancyApp,
    download_cvnfm_instantiate_pkg: None,
    download_cvnfm_upgrade_pkg: None,
):
    """
    JIRA: OTC-14066
    Test function that does the following:
        1. onboard cnf package
        2. verify a new backup is created
        3. stop GR BUR SFTP server
        4. onboard another one package
        5. wait until packages images will be synced between both Active and Passive sites
    """
    onboard_cnf_package(cvnfm_app.cnf_smallstack_pkg)

    gr_app.verify_backup_id_updated_in_availability()

    # make SFTP server unavailable by scaling its replicas to 0
    gr_app.sftp_server.change_server_replicas(replicas=0)

    # onboard another one package
    onboard_cnf_package(cvnfm_app.cnf_upgrade_smallstack_pkg)

    assert (
        gr_app.verify_images_sync_between_registries()
    ), "images synced between Active and Passive site GR docker registries FAILED"


@mark.cvnfm_sftp_unavailable_after_switchover
def test_onboard_second_package_on_new_active_site(
    cvnfm_app: CvnfmApp,
    onboard_cnf_package,
    download_cvnfm_upgrade_pkg: None,
    make_sftp_server_available: None,
):
    """
    JIRA: OTC-14066
    Test function that depends on cvnfm_sftp_unavailable_before_switchover (mark) test of that module and
    should be performed on the new Active Site and does the following:
        1. verify package that was onboarded before SFTP server unavailability exists
        2. verify package that was onboarded after SFTP server unavailability NOT exists
        3. onboard again the second package
    """
    package_id = cvnfm_app.api.packages_client.check_if_package_with_vnfd_id_exists(
        cvnfm_app.cnf_smallstack_pkg.descriptor_id
    )
    assert (
        package_id
    ), "CVNFM package that was onboarded before SFTP server unavailability does NOT exist"
    assert cvnfm_app.api.packages_client.check_package_is_onboarded(
        package_id
    ), "CVNFM package that was onboarded before SFTP server unavailability has NOT been onboarded"
    assert not cvnfm_app.api.packages_client.check_if_package_with_vnfd_id_exists(
        cvnfm_app.cnf_upgrade_smallstack_pkg.descriptor_id
    ), "CVNFM package that was onboarded after SFTP server unavailability EXISTS"

    onboard_cnf_package(cvnfm_app.cnf_upgrade_smallstack_pkg)
