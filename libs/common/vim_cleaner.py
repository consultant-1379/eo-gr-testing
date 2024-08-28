"""Module to store VimCleaner class"""

from core_libs.common.constants import EnvVariables
from core_libs.vim.data.constants import ServerKeys
from core_libs.vim.openstack import OpenStack

from libs.common.asset_names import AssetNames
from libs.common.config_reader import ConfigReader
from libs.common.constants import GR_TEST_PREFIX
from libs.common.custom_exceptions import EnvironmentVariableNotProvidedError
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class VimCleaner:
    """VIM zone cleaner for clean up test assets from specified VIM zone"""

    def __init__(self, config: ConfigReader):
        self._config = config
        self.vim_name = self.__check_and_get_vim_zone_env_var()
        self._openstack = OpenStack(config=self._config)
        self._asset_names = AssetNames()
        self._logger = set_eo_gr_logger_for_class(self)

        # cleaners:
        self._delete_network = self._openstack.networks.delete_network
        self._delete_image = self._openstack.images.delete_image
        self._delete_flavor = self._openstack.flavors.delete_flavor
        self._delete_stack = self._openstack.stacks.delete_stack
        self._delete_server = self._openstack.servers.delete_server

    def __check_and_get_vim_zone_env_var(self) -> str:
        """Check if it was specified vim env var and return its value
        Raises:
            EnvironmentVariableNotProvidedError: when VIM env var is not specified
        Returns:
            vim zone env var value
        """
        if not ENV_VARS.vim:
            raise EnvironmentVariableNotProvidedError(
                f"To use {self.__class__.__name__!r} tool please provide {EnvVariables.VIM!r} env variable."
            )
        return ENV_VARS.vim

    def _filter_openstack_objects_by_gr_prefix(self, objects: list) -> list:
        """Filter openstack objects by GR prefix
        Args:
            objects: list of openstack objects
        Returns:
            list with filtered objects
        """
        self._logger.debug(f"Filter objects by {GR_TEST_PREFIX} prefix")
        result = [item for item in objects if item.name.startswith(GR_TEST_PREFIX)]
        self._logger.debug(f"Result of filtering: {result}")
        return result

    def clean_up_all_by_asset_names(self) -> None:
        """Clean up VIM zone from test assets by full asset names except stacks (VAPP) name.
        Due to multiple stacks can be created during test session, they will be deleted
        if there is shared name in the stack name.
        """
        self._logger.info(
            f"Start attempting to clean up test assets in the {self.vim_name!r} VIM zone, if they exist."
        )
        assets_and_cleaners = []

        # there are possible multiple stacks can be existed with shared name suffix
        for stack in self._filter_openstack_objects_by_gr_prefix(
            self._openstack.stacks.list_stacks()
        ):
            if ENV_VARS.gr_stage_shared_name in stack.name:
                assets_and_cleaners.append((stack.name, self._delete_stack))

        assets_and_cleaners.extend(
            [
                (self._asset_names.openstack_network_name, self._delete_network),
                (self._asset_names.openstack_image_name, self._delete_image),
                (self._asset_names.openstack_flavor_name, self._delete_flavor),
            ]
        )
        for asset, cleaner in assets_and_cleaners:
            if cleaner(asset):
                self._logger.info(f"{asset!r} has been successfully deleted.")
            else:
                self._logger.info(f"Nothing to delete. {asset!r} doesn't exist on vim.")

        self._logger.info(
            f"Cleanup VIM by shared name: {ENV_VARS.gr_stage_shared_name!r} finished successfully."
        )

    def clean_up_all_by_gr_prefix(
        self,
    ) -> None:
        """Cleans up all VIM assets that start with GR prefix"""
        self._logger.info(
            f"Start cleanup {self.vim_name!r} VIM zone from test assets that start with {GR_TEST_PREFIX!r} prefix."
        )
        name_filter = {ServerKeys.NAME: GR_TEST_PREFIX}
        assets_and_cleaners = (
            (self._openstack.stacks.list_stacks, self._delete_stack),
            (
                # Filter servers request by name to increase performance when a lot of servers exist on a VIM,
                # but because 'name' works like an 'in' operator, the response still needs to be filtered by prefix.
                # For all other objects, such filter is either unavailable or works as an "equality" operator.
                lambda: self._openstack.servers.list_servers(name_filter),
                self._delete_server,
            ),
            (self._openstack.networks.list_networks, self._delete_network),
            (self._openstack.images.list_images, self._delete_image),
            (self._openstack.flavors.list_flavors, self._delete_flavor),
        )
        for assets, cleaner in assets_and_cleaners:
            assets = self._filter_openstack_objects_by_gr_prefix(assets())
            if not assets:
                self._logger.info("No assets found to delete.")

            for asset in assets:
                # delete by ID to prevent 'Multiple matches found' exception
                if cleaner(asset.id):
                    self._logger.info(f"{asset.name!r} has been successfully deleted.")
                else:
                    self._logger.warning(
                        f"Something went wrong. {asset.name!r} looks like already deleted. "
                        f"Please check it on {self.vim_name!r} VIM zone."
                    )
        self._logger.info(
            f"Cleanup VIM by {GR_TEST_PREFIX!r} prefix finished successfully."
        )
