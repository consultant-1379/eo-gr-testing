"""Module with DockerRegistryApp class"""
from core_libs.common.constants import CcdConfigKeys
from core_libs.common.custom_exceptions import HttpErrorNotFound
from core_libs.common.decorators import retry_deco
from core_libs.common.misc_utils import sort_object_with_nested_data

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrConfigKeys, DockerRegistryKeys
from libs.common.docker_registry_client import DockerRegistryApiV2Client
from libs.utils.logging.logger import logger


class GrDockerRegistryApp:
    """Class for GR Docker Registry functionality"""

    def __init__(self, config: ConfigReader):
        self.config = config
        self.api_client = DockerRegistryApiV2Client(
            self.gr_host, self.registry_username, self.registry_password
        )

    @property
    def gr_host(self) -> str:
        """GR Host value"""
        return self.config.read_section(GrConfigKeys.GR_HOST)

    @property
    def registry_username(self) -> str:
        """GR Docker registry username"""
        return self.config.read_section(CcdConfigKeys.REGISTRY_USER_NAME)

    @property
    def registry_password(self) -> str:
        """GR Docker registry password"""
        return self.config.read_section(CcdConfigKeys.REGISTRY_USER_PASSWORD)

    @retry_deco(
        HttpErrorNotFound
    )  # for the case when the repository (image) has been created but the tag has not yet been uploaded
    def collect_all_images_with_tags(self) -> list:
        """
        Collect all images with their tags from registry
        Returns:
            list with images and their tags
        """
        logger.info(
            f"Getting images with their tags from the {self.gr_host!r} registry"
        )
        images = self.api_client.get_repositories().get(DockerRegistryKeys.REPOSITORIES)

        return sort_object_with_nested_data(
            [self.api_client.get_image_tags(image) for image in images]
        )
