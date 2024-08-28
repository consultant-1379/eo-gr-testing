"""
Script that covers 4.9 (Optional) Pre-Deployment Step for Sending Alarm Data to an External System of
EO Cloud Native Upgrade Instructions.
"""

from apps.codeploy.codeploy_app import CodeployApp
from libs.common.constants import GrEnvVariables
from libs.utils.logging.logger import logger
from util_scripts.common.common import print_with_highlight, verify_passive_site_env_var
from util_scripts.common.config_reader import active_site_config, passive_site_config

EO_VERSION_WITH_ALARM_SECRET = "2.28.0-200"

if __name__ == "__main__":
    print_with_highlight(
        f"""
{__doc__}
Script is executed only if current EO version < {EO_VERSION_WITH_ALARM_SECRET!r}.\n
Required environment variables:
    - {GrEnvVariables.ACTIVE_SITE}
    - {GrEnvVariables.PASSIVE_SITE}
"""
    )
    verify_passive_site_env_var()

    for config in active_site_config, passive_site_config:
        codeploy_app = CodeployApp(config)
        if codeploy_app.compare_eo_version(EO_VERSION_WITH_ALARM_SECRET, "<"):
            logger.info(
                "Current EO version requires of alarm secret creation. Creating..."
            )
            codeploy_app.create_alarm_secret()
        else:
            print_with_highlight(
                "Skip creating alarm secret due to current EO version does not meet the conditions."
            )
