"""Module that stores script for updating superuser password on vnflcm pod"""

import asyncio

from core_libs.common.constants import CommonConfigKeys
from core_libs.eo.ccd.k8s_data.pods import VNFLCM_SERVICE

from apps.codeploy.codeploy_app import CodeployApp
from libs.common.config_reader import ConfigReader
from libs.common.constants import GrEnvVariables
from libs.common.eo_rv_node.constants import EoNodePaths
from libs.common.eo_rv_node.eo_rv_node import EoRvNode
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight, verify_passive_site_env_var
from util_scripts.common.config_reader import active_site_config, passive_site_config
from util_scripts.common.constants import VnflcmServiceConstants

PASSWORD = "admin123"


async def update_super_user_password(
    config: ConfigReader, change_replicas: bool, env_name: str
) -> None:
    """
    Method that update superuser password using next steps:
        1. Change replicas to 1 only on Passive Site
        2. Connects to eo-node and switching to current env workdir
        3. Copy the script <configure_superuser_password.sh> from eric-vnflcm-service container to working dir
        4. Run the script <configure_superuser_password.sh>
        5. Change replicas to 0 only on passive site
    Args:
        config: ConfigReader instance for environment that should be updated
        change_replicas: True if for STAND_BY site else False
        env_name: name of environment
    """
    codeploy_app = CodeployApp(config)
    eo_node = EoRvNode(config)

    logger.info(f"Update Superuser Password for environment {env_name!r}")

    try:
        work_dir_path = EoNodePaths.WORK_DIR.format(env_name=env_name)
        if change_replicas:
            codeploy_app.change_stateful_set_replicas(VNFLCM_SERVICE, 1, timeout=400)

        vnflcm_pod_name = codeploy_app.k8s_eo_client.get_pod_full_name(VNFLCM_SERVICE)

        update_pass_cmd = (
            f"cd {work_dir_path} "
            f"&& "
            f"kubectl --kubeconfig kube_config/config -n eo-deploy "
            f"cp {vnflcm_pod_name}:{VnflcmServiceConstants.SUPERUSER_PASSWORD_SCRIPT_IN_POD_PATH} "
            f"configure_superuser_password.sh "
            f"&& "
            f"sh configure_superuser_password.sh {PASSWORD} kube_config/config {codeploy_app.namespace}"
        )

        await eo_node.execute_cmd_async(update_pass_cmd)
    finally:
        if change_replicas:
            codeploy_app.change_stateful_set_replicas(VNFLCM_SERVICE, 0)
    logger.info(
        f"Superuser Password for environment {env_name!r} updated successfully!"
    )


async def main() -> None:
    """
    Method that updates superuser password for Active and Passive sites
    """
    env_list = [(active_site_config, False), (passive_site_config, True)]

    async with asyncio.TaskGroup() as tg:
        for config, change_replicas in env_list:
            env_name = config.read_section(CommonConfigKeys.ENV_NAME)
            if config is None:
                raise ValueError(
                    "Config can't be empty. Please provide it using environment variable."
                )
            tg.create_task(
                update_super_user_password(config, change_replicas, env_name),
                name=env_name,
            )


if __name__ == "__main__":
    print_with_highlight(
        "Updating superuser password on vnflcm pod.\n"
        f"""Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}
            - {GrEnvVariables.PASSIVE_SITE}"""
    )
    verify_passive_site_env_var()

    asyncio.run(main())
