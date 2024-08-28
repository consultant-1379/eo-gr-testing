"""
Module that contains class which performs '6.4 Installation of Certificates' procedure
of 'EO Cloud Native Installation Instructions'.

Note: This post-deployment step must be executed only if EVNFM is deployed.

Note: This procedure will become irrelevant when MR IDUN-17187 is implemented.
"""
from functools import partial
from pathlib import Path
from urllib import parse

from core_libs.common.console_commands import CMD
from core_libs.common.constants import CommonConfigKeys, CcdConfigKeys
from core_libs.common.custom_exceptions import ConfigurationNotFoundException
from core_libs.common.file_utils import FileUtils
from core_libs.common.misc_utils import wait_for
from core_libs.eo.ccd.k8s_api_client import K8sApiClient
from core_libs.eo.ccd.k8s_data.pods import EO_AM_ONBOARDING

from libs.common.config_reader import ConfigReader
from libs.common.constants import (
    ROOT_PATH,
    EvnfmConfigKeys,
    DEFAULT_DOWNLOAD_LOCATION,
)
from libs.common.dns_server.dns_checker import DnsChecker
from libs.utils.common_utils import run_shell_cmd
from libs.utils.logging.logger import logger

# directories
CERTIFICATES = Path("certificates")
TRUSTED_DIR = CERTIFICATES / "trusted"

# scripts
ORIGINAL_CERT_MGMT_SCRIPT = (
    "am-integration-charts/Scripts/eo-evnfm/certificate_management.py"
)
CERT_MGMT_SCRIPT = "certificate_management.py"

# certificates
INTERMEDIATE_CERT_PATH = CERTIFICATES / "intermediate-ca.crt"

run_cmd_from_root_dir = partial(run_shell_cmd, cwd=ROOT_PATH)


class InstallCvnfmCertificates:
    """Class to perform '6.4 Installation of Certificates' procedure
    of 'EO Cloud Native Installation Instructions'"""

    def __init__(self, config: ConfigReader, active_site: bool = True):
        self._k8s_eo_client = None
        self.config = config
        self.active_site = active_site

    @property
    def env_name(self):
        """Environment name"""
        return self.config.read_section(CommonConfigKeys.ENV_NAME)

    @property
    def cvnfm_host(self):
        """CVNFM Host"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_HOST)

    @property
    def root_cert(self):
        """Root certificate"""
        return self.config.read_section(CommonConfigKeys.ROOT_CERT)

    @property
    def eo_cnf_cert(self):
        """EO CNF certificate"""
        return self.config.read_section(CommonConfigKeys.EO_CNF_CERT)

    @property
    def pkg_intermediate_cert(self):
        """Package Intermediate certificate"""
        return self.config.read_section(CommonConfigKeys.INTERMEDIATE_CERT)

    @property
    def intermediate_cert(self):
        """Cluster Intermediate certificate"""
        return self.config.read_section(CommonConfigKeys.INTERMEDIATE_CERTIFICATE_PATH)

    @property
    def user_name(self):
        """CVNFM username"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_DEFAULT_USER_NAME)

    @property
    def user_password(self):
        """CVNFM user password"""
        return self.config.read_section(EvnfmConfigKeys.EVNFM_DEFAULT_USER_PASSWORD)

    @property
    def namespace(self):
        """K8s namespace"""
        return self.config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE)

    @property
    def kubeconfig_path(self):
        """K8s config path"""
        return self.config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH)

    @property
    def k8s_client(self):
        """K8s client property"""
        if self._k8s_eo_client is None:
            self._k8s_eo_client = K8sApiClient(
                namespace=self.namespace,
                kubeconfig_path=self.kubeconfig_path,
                download_location=DEFAULT_DOWNLOAD_LOCATION,
            )
        return self._k8s_eo_client

    def install_certificates(self) -> None:
        """
        Main method to run CVNFM certificates installation procedure
        """
        DnsChecker(self.config).check_resolving_host_with_active_site_ip(
            host=self.cvnfm_host
        )
        logger.info(
            f"Starting to run procedure for installation CVNFM certificates for {self.env_name}"
        )
        self.copy_env_cert_and_mgmt_script()
        self.clean_up_trusted_dir()
        self.download_certs_to_trusted_dir()
        self.run_install_cert_mgmt_script()

        logger.info("CVNFM certificates installation has been finished successfully!")

    def copy_env_cert_and_mgmt_script(self) -> None:
        """
        Copy env certificate and management script to certificates directory
        """
        run_cmd_from_root_dir(
            CMD.CP.format(file=ORIGINAL_CERT_MGMT_SCRIPT, dest=CERT_MGMT_SCRIPT)
        )
        run_cmd_from_root_dir(CMD.RM_R.format(CERTIFICATES))
        run_cmd_from_root_dir(CMD.MK_DIR.format(CERTIFICATES))

        if not Path(self.intermediate_cert).exists():
            raise ConfigurationNotFoundException(
                f"Cluster Intermediate certificate is not found by {self.intermediate_cert} path. "
                "Please check environment configuration"
            )

        logger.info(
            f"Copy {self.intermediate_cert} certificate for {self.env_name!r} to certificate directory"
        )
        run_cmd_from_root_dir(
            cmd=CMD.CP.format(file=self.intermediate_cert, dest=INTERMEDIATE_CERT_PATH)
        )

    @staticmethod
    def clean_up_trusted_dir() -> None:
        """
        Prepare trusted dir for certificates installing
        """
        logger.info(f"Cleaning up {TRUSTED_DIR!r} directory")

        run_cmd_from_root_dir(CMD.RM_R.format(TRUSTED_DIR), check_return_code=False)
        run_cmd_from_root_dir(CMD.MK_DIR.format(TRUSTED_DIR))

    def download_certs_to_trusted_dir(self) -> None:
        """
        Download certificates to the trusted directory
        """
        logger.info(f"Download certificates to {TRUSTED_DIR!r} dir")

        for cert in self.eo_cnf_cert, self.pkg_intermediate_cert, self.root_cert:
            FileUtils.download_file(
                url=cert, save_location=TRUSTED_DIR / Path(cert).name
            )

    def _check_certs_on_onboarding_pod(self) -> bool:
        """
        Verifies whether the EO certificates are present on the onboarding pod
        """
        logger.info(
            "Verifies whether the EO certificates are present on the onboarding pod"
        )
        certs_on_pod = ["cert1.pem", "cert2.pem", "cert3.pem"]
        certs = self.k8s_client.exec_in_pod(
            pod=EO_AM_ONBOARDING, cmd=CMD.LS.format("/obs/ca")
        )
        return sorted(certs.split()) == certs_on_pod

    def _build_install_cert_manager_cmd(
        self, cert_mgmt: str, is_eo: bool = False
    ) -> str:
        """
        Builds the installation command depending on the certificate type
        Args:
            cert_mgmt: certificate management file name in the root dir
            is_eo: flag to choose the certificate installation type
        Returns:
            The certificate installation command
        """
        installation_type = f"install-{'eo-' if is_eo else ''}certificates"
        host_name = parse.urlsplit(self.cvnfm_host).hostname

        return CMD.CD_AND_RUN_PYTHON.format(
            dir=ROOT_PATH,
            file=" ".join(
                [
                    cert_mgmt,
                    installation_type,
                    "--login",
                    self.user_name,
                    "--password",
                    self.user_password,
                    "--host",
                    host_name,
                ]
            ),
        )

    def _change_onboarding_deployment_replicas(self, replicas: int) -> None:
        """
        Change number of CVNFM onboarding deployment replicas
        Args:
            replicas: desired number of replicas
        """
        self.k8s_client.scale_deployment_replicas(EO_AM_ONBOARDING, replicas)

    def run_install_cert_mgmt_script(self) -> None:
        """
        Install EO certificates on Active or Passive Sites
        """
        logger.info(f"Run certificates installation {CERT_MGMT_SCRIPT!r} script")

        if not self.active_site:
            # on passive site onboarding pod is scaled to 0
            self._change_onboarding_deployment_replicas(replicas=1)

        try:
            run_cmd_from_root_dir(
                self._build_install_cert_manager_cmd(cert_mgmt=CERT_MGMT_SCRIPT)
            )
            wait_for(self._check_certs_on_onboarding_pod, interval=10, timeout=300)
            run_cmd_from_root_dir(
                self._build_install_cert_manager_cmd(
                    cert_mgmt=CERT_MGMT_SCRIPT, is_eo=True
                )
            )
        finally:
            if not self.active_site:
                self._change_onboarding_deployment_replicas(replicas=0)
