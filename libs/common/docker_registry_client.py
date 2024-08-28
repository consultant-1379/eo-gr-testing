"""Module with DockerRegistryApiV2Client class"""

from http import HTTPStatus
from json import JSONDecodeError
from urllib.parse import urljoin

import requests
from core_libs.common.custom_exceptions import HttpErrorNotFound
from core_libs.common.misc_utils import (
    format_url,
    get_pretty_json,
)

from libs.common.constants import DockerRegistryV2ApiPaths
from libs.common.env_variables import ENV_VARS
from libs.utils.logging.logger import logger


class DockerRegistryApiV2Client:
    """Class to interact with REST Docker Registry V2 API"""

    def __init__(self, registry_host: str, username: str, password: str):
        self.registry_host = format_url(registry_host)
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._session.auth = (self.username, self.password)

    def _request(self, method, url_path: str) -> requests.Response:
        """
        Perform REST API request to registry
        Args:
            method: REST API method
            url_path: url path of registry
        Returns:
            response object
        """
        url = urljoin(self.registry_host, url_path)

        logger.debug(f"Sending {method!r} request to {url}")
        response = self._session.request(method, url, verify=False, timeout=10)

        try:
            response_message = response.json()
        except JSONDecodeError:
            response_message = response.text

        if ENV_VARS.pretty_api_logs:
            response_message = get_pretty_json(response_message)

        logger.debug(
            f"Status code: {response.status_code}\nContent: {response_message}"
        )
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise HttpErrorNotFound(response.text)
        response.raise_for_status()

        return response

    def get(self, url_path: str) -> requests.Response:
        """
        Perform GET method to registry
        Args:
            url_path: url path of registry
        Returns:
            response object
        """
        return self._request(method="GET", url_path=url_path)

    def get_repositories(self) -> dict:
        """
        Get all repositories (images) from registry
        Returns:
            repositories (images)
        """
        logger.info(
            f"Getting all repositories from the {self.registry_host!r} registry"
        )
        return self.get(url_path=DockerRegistryV2ApiPaths.REPOSITORIES).json()

    def get_image_tags(self, repository: str) -> dict:
        """
        Get image's tags from provided repository (image name)
        Args:
            repository: repository name (image name w/o tag)
        Returns:
            image's tags
        """
        logger.info(f"Getting tags for repository (image) {repository!r}")
        return self.get(
            url_path=DockerRegistryV2ApiPaths.TAGS.format(repository=repository)
        ).json()
