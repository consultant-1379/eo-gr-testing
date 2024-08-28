"""Module with common utils"""

from libs.common.constants import GrEnvVariables
from libs.common.custom_exceptions import (
    EnvironmentVariableNotProvidedError,
)
from libs.common.env_variables import ENV_VARS


def print_with_highlight(text: str, sign: str = "-", number_of_signs: int = 20) -> None:
    """Method that print given text with highlights around

    Args:
        text: text to be printed
        sign: sign to highlight. Defaults is "-".
        number_of_signs: number of signs
    """
    signs = f"{sign}" * number_of_signs
    print(f"{signs}\n{text}\n{signs}")


def verify_passive_site_env_var() -> None:
    """Verify if env var for Passive Site provided
    Raises:
        EnvironmentVariableNotProvidedError: when env var not provided
    """
    if not ENV_VARS.passive_site:
        raise EnvironmentVariableNotProvidedError(
            f"{GrEnvVariables.PASSIVE_SITE!r} env variable is required for this script!"
        )
