"""
Module with common fixtures for GR tests
"""

from glob import glob
from os import path
from pathlib import PurePath
from typing import Any

import pytest
from _pytest.fixtures import FixtureRequest

from libs.common.constants import GrEnvVariables, EoVersionsFiles
from libs.common.custom_exceptions import EnvironmentVariableNotProvidedError
from libs.common.env_variables import ENV_VARS
from libs.utils.common_utils import create_file_from_template
from libs.utils.logging.logger import logger


def format_fixture_path(filepath: str) -> str:
    """
    A function that formats the fixture filepath and leaves the filename
    """
    return filepath.replace("/", ".").replace("\\", ".").replace(".py", "")


pytest_plugins = [
    format_fixture_path(fixture)
    for fixture in glob(path.join("tests", "fixtures", "*.py"))
    if "__" not in fixture
]


@pytest.fixture(scope="session")
def is_tests_in_session_failed(request: FixtureRequest) -> callable:
    """
    Fixture that returns status of the test session
    Args:
        request: an object that gives access to the pytest context and options
    Returns:
        function that gets test status: True | False
    """

    def is_tests_failed() -> bool:
        """
        Function that returns status of the test session
        Returns:
            True if tests failed else False
        """
        return bool(request.node.session.testsfailed)

    return is_tests_failed


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Any):
    """
    A hookwrapper that allows to obtain pytest report object

    Note: Creation of versions_report.html file with N/A EO versions
    has been added to prevent exceptions when pytest report rendering
    fails early and EO version is not yet available

    Args:
        item (): pytest item object
    Yields: pytest report object
    """
    create_dumy_eo_versions_if_not_exist()

    test_module_path = PurePath(item.fspath.dirname)
    item.group = "/".join(
        test_module_path.parts[test_module_path.parts.index("tests") + 1 :]
    )
    output = yield
    report = output.get_result()
    report.phase = "Test execution" if report.when == "call" else report.when


@pytest.fixture(scope="session")
def command_line_session_mark(pytestconfig: pytest.Config) -> str:
    """
    Fixture that returns mark(s) that was used in command line (-m option) for running tests.
    Args:
        pytestconfig: Pytest Config instance
    Returns:
        Pytest mark from -m option if exists else empty string
    """
    return pytestconfig.getoption("-m")


@pytest.fixture(scope="session", autouse=True)
def check_passive_site_env_var_provided(request: FixtureRequest) -> None:
    """Checking environment variable for Passive Site is provided. It's mandatory for GR related tests.
    Args:
        request: an object that gives access to the pytest context and options
    """
    if not ENV_VARS.passive_site:
        tests_markers = [
            mark.name for test in request.node.items for mark in test.own_markers
        ]
        if "NON_GR" not in tests_markers:
            err_msg = (
                f"Please provide {GrEnvVariables.PASSIVE_SITE!r} environment variable."
            )
            logger.error(err_msg)
            raise EnvironmentVariableNotProvidedError(err_msg)


def create_dumy_eo_versions_if_not_exist() -> None:
    """
    Creates versions_report.html file with N/A EO versions
    """
    report = EoVersionsFiles.VERSIONS_REPORT
    if not report.is_file():
        n_a = "N/A"
        versions = {
            "eo": n_a,
            "dm": n_a,
            "vmvnfm": n_a,
            "cvnfm": n_a,
        }
        logger.debug(f"Creating {report.name} file and populating it with a dummy data")
        create_file_from_template(EoVersionsFiles.VERSIONS_TEMPLATE, report, versions)
