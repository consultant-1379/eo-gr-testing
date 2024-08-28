"""
    It's service script that defines DNS Server IP for the provided Site
    and creates DNS_FLAG by default.
    When the '--registry' flag is set, the script sets only GLOBAL_REGISTRY env variable.
    Then it writes the data to env.properties file to use it as env vars in Jenkins.

    NOTE: this script intentionally lacks logging to reduce excessive noise in the Jenkins console
"""
import argparse

from core_libs.common.constants import CcdConfigKeys

from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    GrEnvVariables as GrEnvVars,
    ENV_PROPERTIES_FILE,
    DockerFlags,
    GrConfigKeys,
)
from libs.common.env_variables import ENV_VARS
from util_scripts.common.common import print_with_highlight as print_w_h

CONFIG = ConfigReader()
ENV_NAME = ENV_VARS.active_site


def write_to_env_properties_file(content: str) -> None:
    """
    Create the env.properties file and writes there ENV variables
    for the further use as environment variables in Jenkins jobs to run test container
    Args:
        content: A string with an environment variable and its value, e.g.: <ENV_VAR>=<value>
    """
    print_w_h(f"Write a {content=} to the {ENV_PROPERTIES_FILE}")
    with ENV_PROPERTIES_FILE.open(mode="w", encoding="utf-8") as file:
        file.write(content)


def get_dns_env_vars() -> str:
    """
    Defines DNS Server IP for provided Site, creates DNS_FLAG and
    Returns:
        A string with the DNS server IP and DNS flag values
    """
    CONFIG.read_sftp_and_dns(env=ENV_NAME)
    dns_ip = CONFIG.read_section(GrConfigKeys.DNS_SERVER_EX_IP_ADDRESS)

    print_w_h(
        f"Creating {ENV_PROPERTIES_FILE.name} file with {GrEnvVars.DNS_FLAG} and {GrEnvVars.DNS_SERVER_IP} env vars..."
    )
    print_w_h(f"{GrEnvVars.DNS_SERVER_IP!r} for {ENV_NAME!r} environment: {dns_ip!r}.")

    dns_server_ip_content = f"{GrEnvVars.DNS_SERVER_IP}={dns_ip}\n"
    dns_flag_content = f"{GrEnvVars.DNS_FLAG}={DockerFlags.DNS.format(dns_ip)}\n"
    return dns_server_ip_content + dns_flag_content


def get_global_registry() -> str:
    """
    Obtaining a value of GLOBAL_REGISTRY_HOST key from the environment config
    Returns:
        A string with GLOBAL_REGISTRY env variable value
    """
    CONFIG.read_env(env=ENV_NAME)
    registry = CONFIG.read_section(CcdConfigKeys.GLOBAL_REGISTRY_HOST)
    print_w_h(
        f"Creating {ENV_PROPERTIES_FILE.name} file with {GrEnvVars.GLOBAL_REGISTRY} environment variable"
    )
    registry_env_var = f"{GrEnvVars.GLOBAL_REGISTRY}={registry}\n"
    print_w_h(f"ENV variable {registry_env_var} will be set for {ENV_NAME}")
    return registry_env_var


if __name__ == "__main__":
    DESCRIPTION = f"""
    This script creates the env.properties file and write there data for the further use
    as environment variables in Jenkins jobs to run test container.
    By default defines the following ENV variables:
        - {GrEnvVars.DNS_SERVER_IP}
        - {GrEnvVars.DNS_FLAG}
    When the "--registry" flag is set, the script sets only:
        - {GrEnvVars.GLOBAL_REGISTRY}

    Required environment variables:
        - {GrEnvVars.ACTIVE_SITE}: The Environment to read config of
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "--registry",
        action="store_true",
        help="A flag to define Global registry ENV variable only",
    )

    args = parser.parse_args()

    if args.registry:
        write_to_env_properties_file(get_global_registry())
    else:
        write_to_env_properties_file(get_dns_env_vars())
