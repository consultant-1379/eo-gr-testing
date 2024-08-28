"""
Module with Version Collector class
"""

from functools import cached_property

import yaml
from core_libs.common.custom_exceptions import ConfigmapNotFoundException
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.constants import EoApps, InstalledAppConfigMapKeys, EoPackages
from libs.utils.logging.logger import logger

INSTALLED_APP_CONFIGMAP = "eric-installed-applications"


class VersionCollector:
    """
    Class for collection all EO installed application versions
    """

    def __init__(
        self,
        k8s_eo_client: K8sApiClient,
    ):
        self._k8s_eo_client: K8sApiClient = k8s_eo_client
        self.not_installed = "not installed"

    @property
    def collection_versions_for_pytest_reporter(self) -> dict:
        """Collecting all required for pytest reporter EO versions"""
        logger.debug(
            f"Collecting all required for pytest reporter versions from {INSTALLED_APP_CONFIGMAP!r} configmap"
        )
        return {
            "eo": self.eo_version,
            "dm": self.deployment_manager_version,
            "vmvnfm": self.get_version(app_name=EoApps.VMVNFM),
            "cvnfm": self.get_version(app_name=EoApps.CVNFM),
        }

    @cached_property
    def eo_version(self) -> str:
        """EO (HelmFile) version"""
        return self.get_version(package_name=EoPackages.HELM_FILE)

    @cached_property
    def deployment_manager_version(self) -> str:
        """Deployment Manager version"""
        return self.get_version(package_name=EoPackages.DM)

    @cached_property
    def _installed_data(self) -> dict | str:
        """
        Receiving installed EO data from on the cluster from configmap
        Returns:
            dict with installed EO data if configmap exists with installed data, None otherwise
        """
        try:
            config_map = self._k8s_eo_client.get_configmap(INSTALLED_APP_CONFIGMAP)
            installed_data = yaml.safe_load(
                config_map.data[InstalledAppConfigMapKeys.INSTALLED]
            )
            if isinstance(installed_data, dict):
                return installed_data
            else:
                raise TypeError

        except (KeyError, TypeError):
            err_msg = f"versions data was not available in {INSTALLED_APP_CONFIGMAP!r} configmap"
            logger.error(err_msg)
        except ConfigmapNotFoundException:
            err_msg = f"{INSTALLED_APP_CONFIGMAP!r} configmap was not available!"
            logger.error(err_msg)
        return err_msg

    def get_version(
        self, *, package_name: EoPackages | None = None, app_name: EoApps | None = None
    ) -> str:
        """Get version of provided EO package or EO application
        Args:
            package_name: eo package name that provided with EO
            app_name: eo application name that installed with EO
        Returns:
            package or app version if found else text with not found reason
        """
        if not isinstance(self._installed_data, dict):
            return self._installed_data

        if app_name:
            return self._get_app_version(app_name)
        elif package_name:
            return self._get_package_version(package_name)

        raise ValueError("Please provide component or application name.")

    def _get_app_version(self, app_name: EoApps) -> str:
        """
        Returns EO application version installed on the cluster
        Args:
            app_name: eo application name
        Returns:
            app's version if found, otherwise text with not found reason
        """
        csar_apps = self._installed_data.get(InstalledAppConfigMapKeys.CSAR)
        if not csar_apps:
            err_msg = "installed application data was not available"
            logger.error(err_msg)
            return err_msg
        try:
            app = [
                item
                for item in csar_apps
                if item[InstalledAppConfigMapKeys.NAME] == app_name
            ].pop()
            version = app[InstalledAppConfigMapKeys.VERSION]
            logger.info(f"{app_name} version: {version}")
            return version
        except IndexError:
            logger.debug(f"{app_name} not installed")
            return self.not_installed
        except KeyError:
            logger.debug(f"{app_name} version not found")
            return "version not available"

    def _get_package_version(self, package_name: EoPackages) -> str:
        """Get version of EO package
        Args:
            package_name: package name
        Returns:
            package's version if found, otherwise error msg
        """
        try:
            version = self._installed_data[package_name]
            if package_name == EoPackages.HELM_FILE:
                version = version[InstalledAppConfigMapKeys.RELEASE]
            logger.info(f"{package_name} version: {version}")
            return version
        except KeyError:
            err_msg = f"{package_name!r} version was not available!"
            logger.error(err_msg)
            return err_msg
