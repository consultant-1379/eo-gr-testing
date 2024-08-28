"""
A module to store common objects pytest fixtures
"""

from core_libs.vim.openstack import OpenStack
from pytest import fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.cvnfm.cluster import Cluster
from apps.cvnfm.cvnfm_app import CvnfmApp
from apps.gr.geo_redundancy import GeoRedundancyApp
from apps.vim_app import VimApp
from apps.vmvnfm.vmvnfm_app import VmvnfmApp
from libs.common.config_reader import ConfigReader
from libs.common.dns_server.dns_checker import DnsChecker
from libs.common.env_variables import ENV_VARS


@fixture(scope="session")
def cvnfm_app(config_read_active_site: ConfigReader) -> CvnfmApp:
    """
    A pytest fixture that creates a CvnfmApp object
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
    Return:
        CvnfmApp object
    """
    return CvnfmApp(config_read_active_site)


@fixture(scope="session")
def vmvnfm_app(config_read_active_site: ConfigReader) -> VmvnfmApp:
    """
    A pytest fixture that creates a VmvnfmApp object
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
    Return:
        VmvnfmApp object
    """
    return VmvnfmApp(config_read_active_site)


@fixture(scope="session")
def vim_app(config_read_active_site: ConfigReader) -> VimApp:
    """
    A pytest fixture that creates a VimApp object
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
    Returns:
        VimApp object
    """
    return VimApp(config_read_active_site)


@fixture(scope="session")
def cluster_app(config_read_active_site: ConfigReader) -> Cluster:
    """
    A pytest fixture that creates a Cluster object
    :param config_read_active_site: the ConfigReader instance of Active Site
    :return: Cluster object
    """
    return Cluster(config_read_active_site)


@fixture(scope="session")
def codeploy_app_active_site(config_read_active_site: ConfigReader) -> CodeployApp:
    """
    A pytest fixture that creates a CodeployApp object for Active Site
    :param config_read_active_site: the ConfigReader instance of Active Site
    :return: CodeployApp object
    """
    return CodeployApp(config_read_active_site)


@fixture(scope="session")
def codeploy_app_passive_site(config_read_passive_site: ConfigReader) -> CodeployApp:
    """
    A pytest fixture that creates a CodeployApp object for Passive Site
    Args:
        config_read_passive_site: the ConfigReader instance of Passive Site
    Returns:
        CodeployApp object
    """
    return CodeployApp(config_read_passive_site)


@fixture(scope="session")
def openstack_app(config_read_active_site: ConfigReader) -> OpenStack:
    """
    A pytest fixture that initializes an OpenStack wrapper
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
    Returns:
        OpenStack instance
    """
    return OpenStack(config=config_read_active_site)


@fixture(scope="session")
def gr_app(
    config_read_active_site: ConfigReader, config_read_passive_site: ConfigReader
) -> GeoRedundancyApp:
    """
    A pytest fixture that initializes a GeoRedundancyApp instance
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
        config_read_passive_site: the ConfigReader instance of Passive Site
    Returns:
        GeoRedundancyApp instance
    """
    return GeoRedundancyApp(
        active_site_config=config_read_active_site,
        passive_site_config=config_read_passive_site,
        rv_setup=ENV_VARS.is_rv_setup,
    )


@fixture(scope="session")
def dns_checker(config_read_active_site: ConfigReader) -> DnsChecker:
    """A pytest fixture that initializes a DnsChecker instance
    Args:
        config_read_active_site: the ConfigReader instance of Active Site
    Returns:
        DnsChecker instance
    """
    return DnsChecker(active_site_config=config_read_active_site)
