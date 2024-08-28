"""
Module to store CVNFM application-related pytest fixtures
"""
import sys
from pathlib import Path
from typing import Generator, Callable

from core_libs.common.misc_utils import random_string_generator
from pytest import fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.cvnfm.cluster import Cluster
from apps.cvnfm.cvnfm_app import CvnfmApp
from apps.cvnfm.data.constants import PackageFields, PackageStates
from apps.cvnfm.data.cvnfm_artefact_model import CvnfmArtifactModel
from libs.common.asset_names import AssetNames
from libs.common.config_reader import ConfigReader
from libs.common.constants import DEFAULT_DOWNLOAD_LOCATION
from libs.common.dns_server.dns_server_deployer import DNSServerDeployer
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import log_exception, logger


# pylint: disable=unused-argument


@fixture(scope="package", autouse=True)
def check_docker_registry(
    cvnfm_app: CvnfmApp, codeploy_app_active_site: CodeployApp
) -> None:
    """
    Verify docker global and local registries before CVNFM test stages start.
    Fixture check skipped for Windows OS
    Args:
        cvnfm_app: CvnfmApp instance
        codeploy_app_active_site: CodeployApp instance
    """
    if not sys.platform.startswith("win"):
        codeploy_app_active_site.verify_local_and_global_registries_availability(
            cvnfm_app.registry_user_name, cvnfm_app.registry_user_password
        )
    else:
        logger.warning("Global and local registry verification skipped for Windows OS!")


@fixture(scope="module")
def onboard_cnf_package(cvnfm_app: CvnfmApp) -> callable:
    """
    Fixture that return function that onboard CNF package
    """

    def onboard_pkg(package) -> None:
        """
        Function that onboard CNF package
        """
        package.package_id = cvnfm_app.onboard_cnf_package(package)
        package_details = cvnfm_app.api.packages.get_package_by_id(
            package.package_id
        ).json()
        assert (
            package_details.get(PackageFields.OPERATIONAL_STATE)
            == PackageStates.ENABLED
        ), log_exception(f"Expected operationalState is not {PackageStates.ENABLED}")

    return onboard_pkg


@fixture(scope="module")
def instantiate_cnf_package(
    cvnfm_app: CvnfmApp,
    cluster_app: Cluster,
    asset_names: AssetNames,
    codeploy_app_active_site: CodeployApp,
) -> Callable:
    """
    Fixture return function that instantiate CNF package
    Args:
        cvnfm_app: CvnfmApp instance
        cluster_app: Cluster instance
        asset_names: a AssetNames instance
        codeploy_app_active_site: CodeployApp instance
    Returns:
        A function that deploys the provided package with the specified instance name
    """

    def instantiate_pkg(package: CvnfmArtifactModel, instance_name: str | None = None):
        """
        Function that instantiate CNF package
        """

        instance_name = instance_name or asset_names.cnf_instance_name
        cnf_id = cvnfm_app.create_cnf_instance_identifier(
            package.descriptor_id, vapp_name=instance_name
        )
        if package.descriptor_id == cvnfm_app.cnf_smallstack_pkg.descriptor_id:
            cvnfm_app.cnf_id = cnf_id
        else:
            cvnfm_app.unsigned_cnf_id = cnf_id
        instance_id = cvnfm_app.instantiate_cnf(
            cnf_id,
            package.package_id,
            cluster_app.cluster_name,
            instance_name,
        )

        return instance_id

    return instantiate_pkg


@fixture(scope="package")
def register_default_cluster(cluster_app: Cluster, download_kube_config: str) -> None:
    """
    The pytest fixture that registers default cluster if it doesn't exist in the system.
    According to CVNFM limitations, described in SM-135927,
    every first cluster is always default and cannot be deleted
    :param cluster_app: the cluster_app fixture
    :param download_kube_config: fixture that downloads Kubernetes confing
    """
    if not cluster_app.api.clusters_client.check_default_cluster_exists():
        cluster_app.cluster_config_path = download_kube_config
        cluster_app.register_cluster_config()


@fixture(scope="package")
def register_cluster_and_clean_up(
    cluster_app: Cluster, download_kube_config: str, register_default_cluster: None
) -> None:
    """
    The pytest fixture that registers cluster config and removes it
    if the cluster is present after the test run
    :param cluster_app: the cluster_app fixture
    :param download_kube_config: fixture that downloads Kubernetes confing
    :param register_default_cluster: fixture that registers default cluster if it doesn't exist in the system
    """
    old_config_filepath = Path(download_kube_config)
    new_config_filepath = (
        Path(DEFAULT_DOWNLOAD_LOCATION)
        / f"test_cluster_{random_string_generator()}.config"
    )
    new_config_filepath = Path.rename(old_config_filepath, new_config_filepath)
    cluster_app.cluster_config_path = new_config_filepath
    cluster_app.register_cluster_config()


@fixture(scope="module")
def download_cvnfm_instantiate_pkg(cvnfm_app: CvnfmApp) -> None:
    """
    Download Instantiate CVNFM package on file system
    Args:
        cvnfm_app: instance of CVNFM clas
    """
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_smallstack_pkg, is_randomize_vnfd=ENV_VARS.is_randomize_vnfd
    )


@fixture(scope="module")
def download_cvnfm_upgrade_pkg(cvnfm_app: CvnfmApp) -> None:
    """
    Download Upgrade CVNFM package on file system
    Args:
        cvnfm_app: instance of CVNFM clas
    """
    cvnfm_app.download_cnf_package_and_randomize_vnf_id(
        cvnfm_app.cnf_upgrade_smallstack_pkg,
        is_randomize_vnfd=ENV_VARS.is_randomize_vnfd,
    )


@fixture(scope="function")
def onboard_cnf_package_and_clean_up(
    cvnfm_app: CvnfmApp,
    onboard_cnf_package: callable,
    download_cvnfm_instantiate_pkg: None,
) -> Generator:
    """
    Onboards CNF package and cleans it up after the test execution
    Args:
        cvnfm_app: CvnfmApp instance
        onboard_cnf_package: returns a function that onboards the CNF package
        download_cvnfm_instantiate_pkg: a fixture that downloads a CVNFM package to the file system
    """
    onboard_cnf_package(cvnfm_app.cnf_smallstack_pkg)
    yield
    cvnfm_app.delete_cnf_package_if_exists(cvnfm_app.cnf_smallstack_pkg.descriptor_id)


@fixture(scope="function")
def instantiate_cnf_package_and_clean_up(
    cvnfm_app: CvnfmApp,
    register_cluster_and_clean_up: None,
    instantiate_cnf_package: callable,
    onboard_cnf_package_and_clean_up: None,
) -> Generator:
    """
    Instantiates a CNF package
    Args:
        register_cluster_and_clean_up: Registers cluster config and removes it
                                       if the cluster is present after the test run
        cvnfm_app: CvnfmApp instance
        onboard_cnf_package_and_clean_up: Onboards CNF package and cleans it up after the test execution
        instantiate_cnf_package: Returns function that instantiate CNF package
    """
    instantiate_cnf_package(cvnfm_app.cnf_smallstack_pkg)
    yield
    cvnfm_app.terminate_cnf_instance(cvnfm_app.cnf_id)


@fixture(scope="session")
def deploy_dns_server(
    config_read_active_site: ConfigReader, config_read_passive_site: ConfigReader
) -> callable:
    """
    Deploys local DNS (dnsmasq) server on the dedicated in config k8s cluster as deployment
    and updates node-local-dns config map in kube-system namespace of the active site
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
        config_read_passive_site: the ConfigReader instance of Passive Site
    Returns:
        A function that performs all described steps
    """

    def dns_server_func(
        override: list | None = None, docker_config_path: str | None = None
    ) -> None:
        """
        An inner function that deploys local DNS (dnsmasq) server on the
        dedicated host and updates node-local-dns config map
        Args:
            override: a list of strings in a form of '<ICCR_IP>:<host_address>'
            to be overriden in the default DNS server configuration
            docker_config_path: a path to the dockerconfigjson file
        """
        logger.info(
            f"Deploying DNS server with following changes in the default configuration: {override}"
        )
        dns_server = DNSServerDeployer(
            active_site_config=config_read_active_site,
            passive_site_config=config_read_passive_site,
            override=override,
            docker_config_path=docker_config_path,
        )
        dns_server.deploy_server_as_k8s_deployment()

    return dns_server_func
