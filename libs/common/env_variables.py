"""Module that stores Environment Variables properties"""
import os
from functools import cached_property
from typing import Any

from core_libs.common.constants import EnvVariables
from core_libs.common.misc_utils import get_boolean_from_env_var

from libs.common.constants import GrEnvVariables, UtilScriptsEnvVarConst, DEFAULT_NAME
from libs.common.custom_exceptions import EnvironmentVariableNotProvidedError


class EnvironmentVariables:
    """Class that allows to get provided Environment variables"""

    # region Common

    @cached_property
    def active_site(self) -> str:
        """
        Returns value of ACTIVE_SITE environment variable
        This parameter mandatory.
        """
        return self._get_env(GrEnvVariables.ACTIVE_SITE, is_mandatory=True)

    @cached_property
    def passive_site(self) -> str:
        """
        Returns value of PASSIVE_SITE environment variable
        """
        return self._get_env(GrEnvVariables.PASSIVE_SITE)

    @cached_property
    def vim(self) -> str:
        """
        Returns value of VIM environment variable
        """
        return self._get_env(EnvVariables.VIM)

    @cached_property
    def override(self) -> str:
        """Returns value of OVERRIDE environment variable"""
        return self._get_env(EnvVariables.OVERRIDE)

    @cached_property
    def is_rv_setup(self) -> bool:
        """Returns value of RV_SETUP environment variable.
        - Default value is: False
        """

        return self._get_env(
            GrEnvVariables.RV_SETUP, default_val=False, is_bool_var=True
        )

    @cached_property
    def gr_stage_shared_name(self) -> str:
        """
        Returns value of GR_STAGE_SHARED_NAME environment variable
        This variable represent the unique prefix for test assets and it shared between the stages.
        Important: this variable should be the same for one test stage
        - Default value is: default-name
        """
        return self._get_env(
            GrEnvVariables.GR_STAGE_SHARED_NAME, default_val=DEFAULT_NAME
        )

    @cached_property
    def is_collect_eo_versions(self) -> bool:
        """Returns boolean value of EO_VERSIONS_COLLECTION environment variable
        - Default value is: True
        """
        return self._get_env(
            GrEnvVariables.EO_VERSIONS_COLLECTION, default_val=True, is_bool_var=True
        )

    @cached_property
    def pretty_api_logs(self) -> bool:
        """Returns value of PRETTY_API_LOGS environment variable
        - Default value is: False
        """
        return self._get_env(
            EnvVariables.PRETTY_API_LOGS, default_val=False, is_bool_var=True
        )

    @cached_property
    def is_resources_clean_up(self) -> bool:
        """Returns boolean value of RESOURCES_CLEAN_UP environment variable
        - Default value is: True"""
        return self._get_env(
            GrEnvVariables.RESOURCES_CLEAN_UP, default_val=False, is_bool_var=True
        )

    @cached_property
    def dns_server_ip(self) -> str:
        """Return value of DNS_SERVER_IP environment variable"""
        return self._get_env(GrEnvVariables.DNS_SERVER_IP, default_val="")

    @cached_property
    def docker_config(self) -> str:
        """Returns value of the DOCKER_CONFIG environment variable"""
        return self._get_env(GrEnvVariables.DOCKER_CONFIG)

    # endregion

    # region DM

    @cached_property
    def dm_log_level(self) -> str:
        """
        Returns boolean value of DM_LOG_LEVEL environment variable
        - Default value is: INFO
        """
        return self._get_env(GrEnvVariables.DM_LOG_LEVEL, default_val="INFO")

    @cached_property
    def host_local_pwd(self) -> str:
        """Returns value of HOST_LOCAL_PWD environment variable
        Host Local PWD value that needed for running DM commands
        Raises:
            EnvironmentVariableNotProvidedError: if var not provided
        """
        return self._get_env(GrEnvVariables.HOST_LOCAL_PWD, is_mandatory=True)

    @cached_property
    def deployment_manager_docker_image(self) -> str:
        """Returns value of DEPLOYMENT_MANAGER_DOCKER_IMAGE environment variable
        Raises:
            EnvironmentVariableNotProvidedError: if var not provided
        """
        return self._get_env(
            GrEnvVariables.DEPLOYMENT_MANAGER_DOCKER_IMAGE, is_mandatory=True
        )

    @cached_property
    def deployment_manager_version(self) -> str:
        """Returns value of DEPLOYMENT_MANAGER_VERSION environment variable"""
        return self._get_env(GrEnvVariables.DEPLOYMENT_MANAGER_VERSION)

    # endregion

    # region Utils

    @cached_property
    def log_prefix(self) -> str:
        """Returns value of LOG_PREFIX environment variable"""
        return self._get_env(UtilScriptsEnvVarConst.LOG_PREFIX)

    # endregion

    # region EVNFM

    @cached_property
    def is_randomize_vnfd(self) -> bool:
        """Returns boolean value of RANDOMIZE_VNFD environment variable
        - Default value is: False
        """
        return self._get_env(
            EnvVariables.RANDOMIZE_VNFD, default_val=False, is_bool_var=True
        )

    @cached_property
    def is_additional_params_for_change_pkg(self) -> bool:
        """Returns boolean value of ADDITIONAL_PARAM_FOR_CHANGE_PKG environment variable
        - Default value is: False
        """
        return self._get_env(
            EnvVariables.ADDITIONAL_PARAM_FOR_CHANGE_PKG,
            default_val=False,
            is_bool_var=True,
        )

    @cached_property
    def enable_vmvnfm_debug_log_level(self) -> bool:
        """
        Returns boolean value of ENABLE_VMVNFM_DEBUG_LOG_LEVEL environment variable
        - Default value is False
        """
        return self._get_env(
            GrEnvVariables.ENABLE_VMVNFM_DEBUG_LOG_LEVEL,
            default_val=False,
            is_bool_var=True,
        )

    # endregion

    @staticmethod
    def _get_env(
        name: str,
        *,
        default_val: Any = None,
        is_mandatory: bool = False,
        is_bool_var: bool = False,
    ) -> Any:
        """
        Allow to get value of environment variable
        Args:
            name: environment variable name
            default_val: value that should be used when env variable not provided
            is_mandatory: if True rise an exception when environment variable, and it's default value not provided
            is_bool_var: to get boolean value of variable
        Raises:
            EnvironmentVariableNotProvidedError: when expected variable are not provided
        Returns:
            environment variable value
        """
        if is_bool_var:
            value = get_boolean_from_env_var(name, str(default_val))
        else:
            value = os.getenv(name, default_val)

        if not value and is_mandatory:
            raise EnvironmentVariableNotProvidedError(
                f"Expected environment variable: '{name}' not provided"
            )
        return value


ENV_VARS = EnvironmentVariables()
