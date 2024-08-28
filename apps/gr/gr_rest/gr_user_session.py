"""Module to store the GrUserSession class"""

from core_libs.eo.user_session import UserSession

from libs.common.config_reader import ConfigReader
from libs.common.constants import GrConfigKeys


class GrUserSession(UserSession):
    """A class for creating GR user session"""

    def __init__(self, site_config: ConfigReader):
        """Overwrite parent init for getting credentials from config"""
        url = site_config.read_section(GrConfigKeys.GR_HOST)
        username = site_config.read_section(GrConfigKeys.GR_USER_NAME)
        password = site_config.read_section(GrConfigKeys.GR_USER_PASSWORD)

        super().__init__(url=url, username=username, password=password)
