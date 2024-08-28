"""Module to store script for deploy SFTP server for store BUR backups"""
from argparse import ArgumentParser

from core_libs.common.constants import CommonConfigKeys

from apps.codeploy.codeploy_app import CodeployApp
from libs.common.bur_sftp_server.bur_sftp_server import BurSftpServer
from libs.common.config_reader import ConfigReader
from libs.common.constants import GrEnvVariables
from libs.common.iperf_tool.constants import IperfCmds
from libs.common.iperf_tool.iperf_server import IperfToolServer
from libs.utils.common_utils import search_with_pattern
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config, passive_site_config


def check_connection_and_permissions_from_site_cluster_to_sftp_server(
    cluster_codeploy: CodeployApp, sftp: BurSftpServer
) -> None:
    """
    Checking connection from site's cluster to SFTP server via SFTP GR credentials
    and check user permissions.
    Args:
        cluster_codeploy: site's cluster codeploy object
        sftp: sftp server object
    """
    logger.info(
        f"Checking connection from {cluster_codeploy.env_name!r} cluster to {sftp}..."
    )
    cluster_codeploy.connect_master_node().allow_tcp_forwarding()
    test_dir = "./eso/test-permissions-dir"
    with cluster_codeploy.connect_master_node().establish_jump_connection(
        user_name=sftp.user_name,
        host=sftp.server_load_balancer_ip,
        password=sftp.password,
    ) as sftp_server_ssh:
        sftp_cl = sftp_server_ssh.open_sftp()
        logger.info("Connection established successfully.")
        # check user permissions by creating directory
        sftp_cl.mkdir(test_dir)
        sftp_cl.rmdir(test_dir)
        logger.info(
            f"User {sftp.user_name!r} has required permissions for data manipulation on SFTP server."
        )


def verify_bandwidth_between_sftp_and_cluster(
    config: ConfigReader, sftp: BurSftpServer
) -> None:
    """
    Performing verification of prerequisite required before deploying EO app with GR:
    - Minimum 250-Mbps link bandwidth between SFTP server and active or passive clusters.
    For more details refer to CPI "EO Cloud Native Geographical Redundancy Deployment Guide"
    2. Prerequisites.
    Args:
        config: config object
        sftp: sftp server object
    """
    cluster = config.read_section(CommonConfigKeys.ENV_NAME)
    logger.info(f"Starting to measure link bandwidth between {sftp} and {cluster=}...")
    target_value = 250  # Mbps

    with IperfToolServer(config) as iperf:
        iperf_output = sftp.exec_cmd_on_sftp_pod(
            IperfCmds.CLIENT.format(iperf.server_load_balancer_ip)
        )
        search_pattern = r"(\d+)\s*Mbits/sec\s*receiver"
        current_bandwidth = search_with_pattern(
            pattern=search_pattern, text=iperf_output
        )
        logger.info(f"Current bandwidth -> {current_bandwidth} Mbps")

        assert int(current_bandwidth) >= target_value, (
            f"Bandwidth between {sftp} server and {cluster=} less then "
            f"required {target_value} Mbps: {current_bandwidth} Mbps. "
            "Installation EO with GR enabled is not recommended under these conditions."
        )
        logger.info(
            f"Successful! Bandwidth between {sftp} and {cluster=} meets "
            "prerequisite condition for deploy EO with GR enabled."
        )


if __name__ == "__main__":
    print_with_highlight(
        f"""
    Script performs the following actions:
    1. Deploys GR BUR SFTP server on dedicated cluster.
    2. Checks connection to the server from both GR clusters.
    3. Checks SFTP user permissions for data manipulation on the server.
    4. Measures link bandwidth between the SFTP server and both clusters.\n
    Required environment variables:
        - {GrEnvVariables.ACTIVE_SITE}
        - {GrEnvVariables.PASSIVE_SITE}
    """
    )
    parser = ArgumentParser()
    parser.add_argument(
        "--disable-bandwidth-measurement",
        action="store_true",
    )
    disable_bandwidth_measurement = parser.parse_args().disable_bandwidth_measurement

    sftp_server = BurSftpServer(config=active_site_config)
    sftp_server.deploy_server()

    print_with_highlight("Checking connection from both clusters to SFTP server...")
    for site_config in active_site_config, passive_site_config:
        check_connection_and_permissions_from_site_cluster_to_sftp_server(
            cluster_codeploy=CodeployApp(site_config), sftp=sftp_server
        )

    if not disable_bandwidth_measurement:
        print_with_highlight("Verifying bandwidth between SFTP server both clusters...")
        for site_config in active_site_config, passive_site_config:
            verify_bandwidth_between_sftp_and_cluster(site_config, sftp=sftp_server)
    else:
        print_with_highlight(
            "Measuring link bandwidth between the SFTP server and both clusters are disabled."
        )

    print_with_highlight(
        f"Script finished successfully. {sftp_server} is successfully deployed."
    )
