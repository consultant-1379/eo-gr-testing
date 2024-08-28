"""Module with copy KMS Master key script"""

from libs.common.constants import GrEnvVariables
from util_scripts.common.common import print_with_highlight, verify_passive_site_env_var
from util_scripts.common.config_reader import active_site_config, passive_site_config
from util_scripts.gr.libs.kms_key import KmsKey

if __name__ == "__main__":
    print_with_highlight(
        f"""
    Script has been started to copy KMS Master key from Active Site to Passive Site...\n
    Required environment variables:
        - {GrEnvVariables.ACTIVE_SITE}
        - {GrEnvVariables.PASSIVE_SITE}
    """
    )
    verify_passive_site_env_var()
    kms_key = KmsKey(
        active_site_config=active_site_config, passive_site_config=passive_site_config
    )
    print_with_highlight(
        f"Passive Site initial KMS Master key: {kms_key.passive_site_kms_key}"
    )
    kms_key.update_passive_site_with_active_site_kms_key()
