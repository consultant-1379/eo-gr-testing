"""Module to store script that performs Deployment Manager log collection command in EO Node workdir,
then downloads created logs locally and also get VM VNFM server.log and saves it locally"""
import asyncio
from argparse import ArgumentParser

from core_libs.common.constants import CommonConfigKeys
from core_libs.eo.ccd.k8s_data.pod_data import K8sDirectorPods

from apps.gr.data.constants import SiteRoles, GrActiveApps
from apps.gr.gr_rest.gr_rest_api_client import GrRestApiClient
from apps.gr.gr_rest.rest_constants import GrRestKeys
from libs.common.constants import GrEnvVariables, UtilScriptsEnvVarConst
from libs.common.deployment_manager.dm_collect_logs import (
    DeploymentManagerLogCollection,
)
from libs.common.vmvnfm_logging.logs_collector import VmvnfmLogsCollector
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config, passive_site_config


def collect_vmvnfm_logs_for_gr_sites() -> None:
    """Collects VMVNFM logs from gr sites"""
    logger.info(
        f"Start collecting VMVNFM logs for GR site with {SiteRoles.PRIMARY!r} role"
    )
    for config in active_site_config, passive_site_config:
        if not config:
            continue

        site_name = config.read_section(CommonConfigKeys.ENV_NAME)
        logger.info(f"Checking {site_name!r} site role...")
        metadata = GrRestApiClient(site_config=config).get_metadata()

        if SiteRoles.PRIMARY == metadata[GrRestKeys.ROLE]:
            logger.info(f"{site_name!r} has {SiteRoles.PRIMARY!r} role")

            if GrActiveApps.VMVNFM in metadata[GrRestKeys.ACTIVE_APPS]:
                log_collector = VmvnfmLogsCollector(config)
                log_collector.get_and_save_server_log()
                log_collector.get_and_save_workflow_cli_log()
                log_collector.get_and_save_apache_logs()
            else:
                logger.warning(
                    f"Skipping collect VMVNFM logs due to VMVNFM is not installed on the {site_name!r} site."
                )
        else:
            logger.warning(
                f"Skipping collect VMVNFM logs due to {site_name!r} is not {SiteRoles.PRIMARY!r} site."
            )


async def collect_dm_logs_from_both_sites() -> None:
    """Method that run log collection in parallel on provided sites"""
    async with asyncio.TaskGroup() as tg:
        for config in active_site_config, passive_site_config:
            if config:
                # asynchronous execute collecting of dm logs
                dm_logs = DeploymentManagerLogCollection(config)
                tg.create_task(
                    dm_logs.generate_and_download_log_files(),
                    name=f"{dm_logs.workdir_env_name}-dm-logs",
                )


if __name__ == "__main__":
    print_with_highlight(
        f"""
    Start script for collecting logs by Deployment Manager tool and from {K8sDirectorPods.ERIC_VNFLCM_SERVICE!r} pod\n
        Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}
        Optional:
            - {GrEnvVariables.PASSIVE_SITE}
            - {UtilScriptsEnvVarConst.LOG_PREFIX}
            - {GrEnvVariables.DEPLOYMENT_MANAGER_VERSION}
        """
    )

    parser = ArgumentParser()
    parser.add_argument(
        "--skip-vmvnfm-logs",
        action="store_true",
    )

    asyncio.run(collect_dm_logs_from_both_sites())

    if not parser.parse_args().skip_vmvnfm_logs:
        collect_vmvnfm_logs_for_gr_sites()

    print_with_highlight("The script has been completed successfully!")
