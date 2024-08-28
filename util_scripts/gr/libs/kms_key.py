"""Module to store KmsKey class and script for copy KMS Master key from Active to Passive Site"""

from core_libs.common.constants import CcdConfigKeys
from core_libs.common.constants import K8sKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.config_reader import ConfigReader
from util_scripts.common.common import print_with_highlight
from util_scripts.common.constants import KMS_SECRET


class KmsKey:
    """Class to execute the firsts step of '5.5.3 Geographical Redundancy Switchover'
    of 'EO Cloud Native Geographical Redundancy Deployment Guide'.

    It allows to copy KMS Master key from Original Active Site to Passive Site."""

    def __init__(
        self, active_site_config: ConfigReader, passive_site_config: ConfigReader
    ):
        self._k8s_client_active_site = self.__init_k8s_client(active_site_config)
        self._k8s_client_passive_site = self.__init_k8s_client(passive_site_config)

    @property
    def passive_site_kms_key(self) -> str:
        """KMS Master key from Passive Site
        Returns:
            KMS Master key from Passive Site
        """
        return self._get_kms_key(active_site=False)

    @property
    def active_site_kms_key(self) -> str:
        """KMS Master key from Original Active Site
        Returns:
            KMS Master key from Active Site
        """
        return self._get_kms_key(active_site=True)

    def update_passive_site_with_active_site_kms_key(self):
        """Update Passive Site Secret with KMS Master key from Active Site"""
        print_with_highlight("Copy KMS Master key from Active Site to Passive Site...")

        self._k8s_client_passive_site.patch_secret(
            name=KMS_SECRET, data={K8sKeys.KEY: self.active_site_kms_key}
        )
        print_with_highlight(
            "Passive Site has been updated with Active Site KMS Master key"
        )

    @staticmethod
    def __init_k8s_client(config: ConfigReader) -> K8sApiClient:
        """Initialize K8s client by provided config
        Returns:
            initialized client
        """
        namespace = config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE)
        kubeconf = config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH)

        return K8sApiClient(namespace, kubeconf)

    def _get_kms_key(self, *, active_site: bool) -> str:
        """Method for parce KMS Master key value from KMS secret
        Args:
            active_site: if True KMS key get from Active Site unless from Passive
        Raises:
            ValueError: when KMS key is empty in secret data
        Returns:
            KMS Master key
        """
        k8s_client = (
            self._k8s_client_active_site
            if active_site
            else self._k8s_client_passive_site
        )
        print_with_highlight(
            f"Getting KMS Master key from the {'Active' if active_site else 'Passive'} Site..."
        )
        if kms_key := k8s_client.get_secret(KMS_SECRET).data.get(K8sKeys.KEY):
            print_with_highlight(f"KMS Master key: {kms_key!r}")

            return kms_key

        raise ValueError(f"KMS Master key not found in {KMS_SECRET!r} secret!")
