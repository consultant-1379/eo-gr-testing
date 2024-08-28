"""Script that deploys a docker image with the DNS (dnsmasq) server on the dedicated in config k8s cluster"""
from argparse import ArgumentParser

from libs.common.constants import GrEnvVariables
from libs.common.dns_server.dns_server_deployer import DNSServerDeployer
from libs.common.env_variables import ENV_VARS
from util_scripts.common.common import print_with_highlight, verify_passive_site_env_var
from util_scripts.common.config_reader import active_site_config, passive_site_config

if __name__ == "__main__":
    DESCRIPTION = f"""
    The following script sets up a DNS server by deploying it on k8s cluster as deployment.
    Required environment variables:
        - {GrEnvVariables.ACTIVE_SITE}
        - {GrEnvVariables.PASSIVE_SITE}
    Optional environment variables:
        - {GrEnvVariables.DOCKER_CONFIG}
    Script options:
        --docker-config
        --override
        --clean-up
    """
    print_with_highlight(DESCRIPTION)

    verify_passive_site_env_var()

    parser = ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "--docker-config",
        type=str,
        default=ENV_VARS.docker_config,
        help="Docker config file used for authentication on the registry",
    )
    parser.add_argument(
        "--override",
        type=list,
        nargs="*",
        default=[],
        help="""
            Allows adding or overriding a hosts list with a custom ICCR_IP. 
            Takes one or more strings delimited with a whitespace where the 
            ICCR_IP and hosts are separated with ':', e.g.: '<ICCR_IP>:<host_address>'
        """,
    )
    parser.add_argument(
        "--clean-up",
        action="store_true",
        help="""
            A flag that should be used to clean up the DNS server container 
            and all its data from the active site config map
        """,
    )
    args = parser.parse_args()

    dns_server = DNSServerDeployer(
        active_site_config=active_site_config,
        passive_site_config=passive_site_config,
        override=args.override,
        docker_config_path=args.docker_config,
    )
    if args.clean_up:
        dns_server.remove_and_clean_up_dns_k8s_server()
    else:
        dns_server.deploy_server_as_k8s_deployment()
