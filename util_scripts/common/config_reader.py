"""
Module to store function to read environment, vim and common configuration
"""

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrConfigKeys, GrEnvVariables
from libs.common.dns_server.dns_checker import DnsChecker
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import logger


def read_active_site_config(env_name: str | None = None) -> ConfigReader:
    """
    Method to read environment, vim and common configuration of ACTIVE_SITE
    Args:
        env_name: parameter to set the environment name
                  instead of reading the ACTIVE_SITE variable
    Returns:
        the instance of ConfigReader class
    """
    env = env_name or ENV_VARS.active_site
    config = ConfigReader()
    config.read_all(env=env, vim=ENV_VARS.vim)
    config.override_config(ENV_VARS.override)

    return config


def read_passive_site_config(env_name: str | None = None) -> ConfigReader | None:
    """
    Method to read environment, vim and common configuration of PASSIVE_SITE
    Args:
        env_name: The name of a passive GR environment which may be set instead of the PASSIVE_SITE variable
    Returns:
        the instance of ConfigReader class or None if not provided
    """
    env = env_name or ENV_VARS.passive_site
    if env:
        config = ConfigReader()
        config.read_all(env=env, vim=ENV_VARS.vim)
        return config
    logger.warning(
        f"Passive site config not provided reading is skipped. "
        f"In case required, provide environment {GrEnvVariables.PASSIVE_SITE} variable please!"
    )
    return None


def read_original_primary_site_config() -> ConfigReader | None:
    """Method returns original site config

    Returns:
        original site config or None if passive site not available
    """
    if active_site_config.read_section(
        GrConfigKeys.GR_ORIGINAL_PRIMARY, default_value=False
    ):
        return active_site_config
    return passive_site_config


active_site_config = read_active_site_config()
# checking DNS setting
DnsChecker(active_site_config).verify_dns_environment_configuration_prerequisites()

passive_site_config = read_passive_site_config()
original_primary_site = read_original_primary_site_config()
