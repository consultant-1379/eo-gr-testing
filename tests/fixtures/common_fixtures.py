"""
module to store common pytest fixtures
"""
from pathlib import Path

from core_libs.common.file_utils import FileUtils
from core_libs.eo.ccd.k8s_data.pods import API_GATEWAY
from pytest import fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.cvnfm.cluster import Cluster
from apps.cvnfm.data.constants import CvnfmDefaults
from apps.gr.data.constants import GrBurOrchestratorDeploymentEnvVars
from libs.common.asset_names import AssetNames
from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    DEFAULT_DOWNLOAD_LOCATION,
    EoVersionsFiles,
)
from libs.common.dns_server.dns_checker import DnsChecker
from libs.common.env_variables import ENV_VARS
from libs.common.thread_runner import ThreadRunner
from libs.common.versions_collector import VersionCollector
from libs.utils.logging.logger import logger
from libs.utils.common_utils import create_file_from_template


# region auto-use fixtures:


@fixture(autouse=True)
def pretty_test_info(request):
    """
    A pytest fixture that prints TEST started with a test name before each test
    and TEST finished with a test name after each test
    """
    test_name = str(request.node.name)
    test_started_msg = f"TEST started: {test_name}"
    test_finished_msg = f"TEST finished: {test_name}"
    logger.info(f" -->> {test_started_msg}")
    yield
    logger.info(f" -->> {test_finished_msg}")


@fixture(scope="session", autouse=True)
def create_downloads_and_cleanup():
    """
    Creates default downloads folder before test session and removes it after test session
    """
    FileUtils.create_folder(DEFAULT_DOWNLOAD_LOCATION)
    yield
    FileUtils.delete_dir(DEFAULT_DOWNLOAD_LOCATION)


@fixture(scope="session", autouse=True)
def populate_eo_versions(codeploy_app_active_site: CodeployApp) -> None:
    """
    Creates the versions_report.html file with current EO versions
    1. Collect EO components versions
    2. Reads and renders eo_versions.html
    3. Creates or overrides versions_report.html with the rendered data
    Args:
        codeploy_app_active_site: CodeployApp instance
    """
    if ENV_VARS.is_collect_eo_versions:
        versions_template = EoVersionsFiles.VERSIONS_TEMPLATE
        versions_report = EoVersionsFiles.VERSIONS_REPORT
        version_collector = VersionCollector(
            k8s_eo_client=codeploy_app_active_site.k8s_eo_client,
        )
        create_file_from_template(
            versions_template,
            versions_report,
            version_collector.collection_versions_for_pytest_reporter,
        )


@fixture(scope="session", autouse=True)
def check_dns_environment_configuration_prerequisites(
    dns_checker: DnsChecker,
) -> None:
    """
    Checking DNS configurations for provided Active Site
    Args:
        dns_checker: DnsChecker instance
    """
    dns_checker.verify_dns_environment_configuration_prerequisites()


# endregion


@fixture(scope="session")
def config_read_active_site(override_config_options: str) -> ConfigReader:
    """
    A pytest fixture that creates a ConfigReader object and reads all given configuration files: common, env, vim
    :param override_config_options: a fixture that returns values that should be overridden
    :return: ConfigReader object
    """
    logger.info("Reading Active Site configuration...")
    config = ConfigReader()
    config.read_all(env=ENV_VARS.active_site, vim=ENV_VARS.vim)
    config.override_config(ENV_VARS.override or override_config_options)

    return config


@fixture(scope="session")
def config_read_passive_site() -> ConfigReader:
    """
    A pytest fixture that creates a ConfigReader object and reads configuration files for Passive Site GR env
    Returns:
        ConfigReader object
    """
    logger.info("Reading Passive Site configuration...")
    config = ConfigReader()
    config.read_env(env=ENV_VARS.passive_site)
    return config


@fixture(scope="session")
def download_kube_config(codeploy_app_active_site):
    """
    Obtains kube config data from the director VM and saves it into config file
    """
    config_data = codeploy_app_active_site.k8s_eo_client.kubeconfig
    file_path = (
        Path(DEFAULT_DOWNLOAD_LOCATION) / CvnfmDefaults.DEFAULT_CISM_CLUSTER_NAME
    )
    FileUtils.save_data_to_yaml_file(
        data=config_data,
        file_path=file_path,
    )
    yield file_path


@fixture(scope="session")
def register_default_kube_cluster(
    cluster_app: Cluster, download_kube_config: str
) -> None:
    """
    The pytest fixture that registers default Kubernetes cluster if it doesn't exist in the system.
    According to CVNFM limitations, described in SM-135927,
    every first cluster is always default and cannot be deleted
    """
    if not cluster_app.api.clusters_client.check_default_cluster_exists():
        logger.info("The default Kubernetes cluster hasn't been found. Registering...")
        cluster_app.cluster_config_path = download_kube_config
        cluster_app.register_cluster_config()


@fixture(scope="session")
def decrease_backup_cycle_interval_on_both_sites(
    codeploy_app_active_site: CodeployApp,
    codeploy_app_passive_site: CodeployApp,
) -> None:
    """
    Change default interval value for creating backup on both sites
    Args:
        codeploy_app_active_site: Active Site CodeployApp instance
        codeploy_app_passive_site: Passive Site CodeployApp instance
    """
    value = "100"
    logger.info(
        f"Changing {GrBurOrchestratorDeploymentEnvVars.GR_PRIMARY_CYCLE_INTERVAL} value to {value!r} "
        "on BUR Orchestrator on both sites"
    )
    threads = []
    for site in codeploy_app_active_site, codeploy_app_passive_site:
        thread = ThreadRunner(
            target=site.update_bur_orchestrator_deployment_env_variable,
            args=(GrBurOrchestratorDeploymentEnvVars.GR_PRIMARY_CYCLE_INTERVAL, value),
            daemon=True,
        )
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join_with_result(timeout=5 * 60)


@fixture(scope="session")
def restart_api_gw_pod(
    codeploy_app_active_site: CodeployApp,
) -> None:
    """
    Workaround for EO versions prior 2.28.0-52.
    The issue EO-170463 is fixed in EO 24.04 Sprint release candidate ver 2.28.0-52,
    before this version the issue "install certificates for signed CNF packages after a switchover" exists
    and requires a workaround - restart of the api-gateway pod after a switchover before certificates installation.
    Args:
        codeploy_app_active_site:  Active Site CodeployApp instance
    """
    eo_with_fix = "2.28.0-52"
    is_eo_with_fix = codeploy_app_active_site.compare_eo_version(eo_with_fix)
    if not is_eo_with_fix:
        codeploy_app_active_site.k8s_eo_client.delete_pod(pod=API_GATEWAY)


@fixture(scope="session")
def asset_names(command_line_session_mark: str) -> AssetNames:
    """A pytest fixture that initializes an AssetNames instance used to share
        test asset names across the tests
    Args:
        command_line_session_mark: fixture that returns value of pytest -m option for current test session
    Returns:
        an AssetNames instance
    """
    return AssetNames(session_mark=command_line_session_mark)
