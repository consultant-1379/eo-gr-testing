"""Store pytest fixtures related to EVNFM functionality"""

from pytest import fixture

from libs.common.config_reader import ConfigReader
from libs.common.constants import EvnfmConfigKeys
from libs.common.dns_server.dns_checker import DnsChecker
from libs.utils.logging.logger import logger


@fixture(scope="session", autouse=True)
def check_dns_settings(
    config_read_active_site: ConfigReader,
    dns_checker: DnsChecker,
) -> None:
    """Check if EVNFM host is resolved by DNS with relevant Active Site ICCR IP
    Args:
        config_read_active_site: Active Site ConfigReader instance
        dns_checker: DnsChecker instance
    """
    logger.info("Checking DNS settings for EVNFM...")
    evnfm_host = config_read_active_site.read_section(EvnfmConfigKeys.EVNFM_HOST)

    dns_checker.check_resolving_host_with_active_site_ip(host=evnfm_host)
