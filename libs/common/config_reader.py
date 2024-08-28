"""
This class defines helper class for reading of yml configs.
"""
from functools import cached_property
from typing import Any

import yaml
from core_libs.common.config_reader import ConfigReader as BaseConfigReader
from core_libs.common.constants import ArtefactConfigKeys
from core_libs.common.custom_exceptions import ConfigurationNotFoundException

from libs.common.artefacts_model_builder import ArtefactsBuilder
from libs.common.constants import ConfigFilePaths, YamlTags
from libs.utils.common_utils import from_key_constructor
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class ConfigReader(BaseConfigReader):
    """
    This class defines helper class for reading of yml configs.
    """

    def __init__(self, config_file_path: str = ConfigFilePaths.COMMON_CONFIG):
        """Init method
        Args:
            config_file_path: path to a config file
        """
        super().__init__(config_file_path)
        self.config = {}
        self.logger = set_eo_gr_logger_for_class(self)
        yaml.add_constructor(tag=YamlTags.FROM_KEY, constructor=from_key_constructor)

    @cached_property
    def artefacts(self) -> ArtefactsBuilder:
        """Get artefacts in model view for all artefact app types"""
        if conf_artefacts := self.read_section(ArtefactConfigKeys.ARTEFACTS, None):
            return ArtefactsBuilder(conf_artefacts)
        return ArtefactsBuilder(self.read_artefacts())

    def read_all(self, env: str, vim: str | None) -> None:
        """Method to read all configuration types: common, env, vim, artefacts, sftp, dns
        Args:
            env: environment name
            vim: vim name
        """
        self.read_common()
        self.read_env(env)
        self.read_vim(vim)
        self.read_artefacts()
        self.read_sftp_and_dns(env)

    def __override_nested_section_by_path(
        self, section_names: list, new_value: Any
    ) -> None:
        """Method to update value for provided section from configuration file
        Args:
            section_names: list of section names for inner section to update from configuration
            new_value: value to update in configuration
        """
        self.logger.info(f"Update config by config path: {section_names!r}")

        root_key = section_names.pop(0)
        current = self.config.get(root_key)
        if not current:
            self.logger.debug(
                f"Ignoring override operation as root key '{root_key}' is not in configuration"
            )
            return None

        for key in section_names:
            if key in current:
                if not isinstance(current[key], dict):
                    current[key] = new_value
                    self.logger.info(
                        f"Overriding key '{key}' by path {section_names}. New value = {new_value}"
                    )
                current = current[key]
            else:
                self.logger.debug(
                    f"Ignoring override key '{key}' value '{new_value}' as it is not in configuration"
                )
        return None

    def override_config(self, override_config: str = "") -> None:
        """Method to update common_config with override variable
        Args:
            override_config: config to override
        """
        parsed_override = {}
        inner_path_ptrn = "|"
        if not override_config:
            self.logger.debug("Skipping override option as it not enabled")
            return None

        try:
            override_config = override_config.replace(" ", "")
            for item in override_config.split("#"):
                parameter, value = tuple(item.split("="))
                parsed_override.update({parameter: value})
                self.logger.debug(f"OVERRIDE: {parsed_override}")
        except ValueError:
            self.logger.error(
                "Exceptions occurred while OVERRIDE values being evaluated"
            )

        for key, value in parsed_override.items():
            if inner_path_ptrn in key:
                keys_list = key.split(inner_path_ptrn)
                self.__override_nested_section_by_path(keys_list, value)
            elif key in self.config.keys():
                self.config[key] = value
                self.logger.info(
                    f"Overriding common_config key '{key}'. New value = {value}"
                )
            else:
                self.logger.debug(
                    f"Ignoring override key '{key}' value '{value}' as it is not in configuration"
                )
        return None

    def read_common(self) -> None:
        """Method to read common_config from yaml file
        Raises:
             ConfigurationNotFoundException: if common config file is not found
        """
        self.logger.info("Reading COMMON configuration")

        if not ConfigFilePaths.COMMON_CONFIG.exists():
            raise ConfigurationNotFoundException(
                f"The configuration file {ConfigFilePaths.COMMON_CONFIG} not found"
            )
        self.config |= self.read_yml(file_path=ConfigFilePaths.COMMON_CONFIG)

    def read_env(self, env: str) -> None:
        """Method to read env_config from yaml file
        Args:
            env: environment name
        Raises:
            ValueError: when provided env name is empty or None
        """
        if not env:
            raise ValueError("Environment name can't be empty!")

        self.logger.info(f"Reading Environment (Site) configuration for {env}")

        if conf_file := list(
            ConfigFilePaths.ENVS_FOLDER.glob(
                f"**/{ConfigFilePaths.ENV_CONF.format(env)}"
            )
        ):
            conf_file = conf_file.pop()
            self.logger.debug(
                f"Environment (Site) configuration for {env!r} is found: {conf_file}"
            )
            self.config |= self.read_yml(file_path=conf_file)
        else:
            self.logger.warning(
                f"The env config file for {env} was not found. Will use common config instead"
            )

    def read_vim(self, vim: str | None) -> None:
        """Method to read vim_config from yaml file
        Args:
            vim: vim name
        """
        if vim:
            self.logger.info(f"Reading VIM configuration for {vim!r}")
            vim_conf_file = (
                ConfigFilePaths.VIMS_FOLDER
                / ConfigFilePaths.VIM_CONF.format(vim.lower())
            )
            if vim_conf_file.exists():
                self.logger.debug(
                    f"VIM configuration for {vim!r} is found: {vim_conf_file}"
                )
                vim_config = self.read_yml(file_path=vim_conf_file)
                vim_config["vim"] = vim
                self.config |= vim_config
            else:
                self.logger.warning(
                    f"The vim config file for {vim!r} was not found. Will use common config instead"
                )
        else:
            self.logger.info(
                "Ignoring VIM configuration as no VIM environment variable set"
            )

    def read_sftp_and_dns(self, env: str | None) -> None:
        """Method to read SFTP and DNS configuration from yaml file
        Args:
            env: environment name
        """
        if env:
            self.logger.info(f"Reading SFTP & DNS configuration for {env!r}")

            if conf_files := list(
                ConfigFilePaths.SFTP_AND_DNS_FOLDER.glob(f"sftp_dns*{env}*")
            ):
                conf_file = conf_files.pop()
                self.logger.info(
                    f"SFTP & DNS configuration is found in {conf_file.name!r} file"
                )
                self.config |= self.read_yml(file_path=conf_file)
            else:
                self.logger.debug(f"SFTP & DNS configuration is NOT found for {env!r}")
        else:
            self.logger.debug(
                "Ignoring SFTP & DNS configuration as NO environment provided"
            )

    def read_artefacts(self) -> dict:
        """Reads artefacts configuration files
        Raises:
            FileNotFoundError: when artefacts config file was not found
        Returns:
            artefacts from config file
        """
        self.logger.info("Reading artefacts configuration")
        artefacts = self.read_yml(file_path=ConfigFilePaths.ARTEFACTS)
        self.config[ArtefactConfigKeys.ARTEFACTS] = artefacts
        return artefacts
