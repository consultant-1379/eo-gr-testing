"""
Module to keep commonly used pytest options
"""
from pytest import fixture

from libs.utils.logging.logger import logger


class PytestOptions:
    """
    Pytest option constants
    """

    OVERRIDE = "--override"


def pytest_addoption(parser):
    """Function that allows to add test run options"""
    parser.addoption(
        PytestOptions.OVERRIDE,
        action="store",
        default="",
        help="Defines configs that should be overridden.",
    )


@fixture(scope="session")
def override_config_options(request):
    """Fixture that handles override option"""
    override_options = request.config.getoption(PytestOptions.OVERRIDE)
    logger.info(f"Override options are: {override_options}")
    return override_options
