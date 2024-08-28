"""
Module that contains base Geographical Redundancy functions
"""

from core_libs.common.constants import CommonConfigKeys

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrConfigKeys
from libs.common.deployment_manager.deployment_manager_client import (
    DeploymentManagerClient,
)


class GeoBase(DeploymentManagerClient):
    """
    Class that contains base Geo Redundancy functions
    """

    def __init__(
        self,
        active_site_config: ConfigReader,
        passive_site_config: ConfigReader,
        rv_setup: bool,
    ):
        super().__init__(active_site_config, rv_setup=rv_setup)
        self.active_site_config = self._config
        self.passive_site_config = passive_site_config
        self._origin_site_config = None
        self.workdir_env_name = self.original_site_name

    @property
    def gr_active_site_host(self):
        """GR Active Site host"""
        return self.active_site_config.read_section(GrConfigKeys.GR_HOST)

    @property
    def gr_passive_site_host(self):
        """GR Passive Site host"""
        return self.passive_site_config.read_section(GrConfigKeys.GR_HOST)

    @property
    def origin_site_config(self):
        """Original primary site config.
        Be careful during the usage as this config!
        It's not changed and always return config setting of environment that has
        env var GR_ORIGINAL_PRIMARY set to True.
        """
        if not self._origin_site_config:
            if self.active_site_config.read_section(GrConfigKeys.GR_ORIGINAL_PRIMARY):
                self._origin_site_config = self.active_site_config
            else:
                self._origin_site_config = self.passive_site_config
        return self._origin_site_config

    @property
    def original_site_name(self):
        """Original site name"""
        return self.origin_site_config.read_section(CommonConfigKeys.ENV_NAME)
