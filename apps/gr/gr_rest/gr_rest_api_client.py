"""Module to store the GrRestApiClient class"""

from apps.gr.gr_rest.gr_mgmt import GrApiMgmt
from apps.gr.gr_rest.gr_user_session import GrUserSession
from libs.common.config_reader import ConfigReader
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class GrRestApiClient:
    """A class for interacting with the GR REST API"""

    def __init__(self, site_config: ConfigReader):
        _session = GrUserSession(site_config=site_config)
        self._logger = set_eo_gr_logger_for_class(self)

        self.mgmt = GrApiMgmt(session=_session)

    def get_metadata(self) -> dict:
        """Get cluster (site) metadata
        Returns:
            cluster (site) metadata object
        """
        self._logger.info("Getting cluster metadata")
        return self.mgmt.get_metadata().json()
