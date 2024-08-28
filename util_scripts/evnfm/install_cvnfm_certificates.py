"""
Module that contains script which performs '6.4 Installation of Certificates' procedure
of 'EO Cloud Native Installation Instructions'.

Note: This post-deployment step must be executed only if EVNFM is deployed.

Note: This procedure will become irrelevant when MR IDUN-17187 is implemented.
"""

from libs.common.constants import GrEnvVariables
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config
from util_scripts.evnfm.libs.install_cvnfm_certificates import InstallCvnfmCertificates

if __name__ == "__main__":
    print_with_highlight(
        f"""
Installation CVNFM certificates on the Active site...\n
Required environment variables:
    - {GrEnvVariables.ACTIVE_SITE}
"""
    )
    print_with_highlight("Installing for Active Site")
    InstallCvnfmCertificates(active_site_config).install_certificates()
