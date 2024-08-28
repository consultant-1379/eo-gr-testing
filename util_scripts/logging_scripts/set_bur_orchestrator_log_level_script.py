"""Module to store script for change log level for GR BUR Orchestrator"""

from core_libs.eo.ccd.k8s_data.pods import ERIC_GR_BUR_ORCH

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.data.constants import GrBurOrchestratorDeploymentEnvVars
from libs.common.constants import GrEnvVariables
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config

LOG_LEVEL = "debug"


def set_bur_orchestrator_log_level(level: str) -> None:
    """Set desired log level for GR BUR Orchestrator
    Args:
        level: log level
    """
    print_with_highlight(f"Setting log level -> {level!r}")
    CodeployApp(active_site_config).update_bur_orchestrator_deployment_env_variable(
        env_var=GrBurOrchestratorDeploymentEnvVars.LOG_LEVEL, value=level
    )
    print_with_highlight(
        f"Log level for {ERIC_GR_BUR_ORCH.name!r} is changed to -> {level!r}"
    )


if __name__ == "__main__":
    print_with_highlight(
        f"""
        Start script for set {LOG_LEVEL.upper()!r} for {ERIC_GR_BUR_ORCH.name!r}.\n
        Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}: The Environment for which needed collect logs
        """
    )
    set_bur_orchestrator_log_level(level=LOG_LEVEL)
    print_with_highlight("Script has been finished successfully!")
