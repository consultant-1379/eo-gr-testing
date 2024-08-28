"""Module that stores CvnfmNamespaceDeleter class for deleting cnf namespaces from cluster"""

from core_libs.common.custom_exceptions import NamespaceNotFoundException

from apps.codeploy.codeploy_app import CodeployApp
from libs.common.asset_names import AssetNames
from libs.common.config_reader import ConfigReader
from libs.utils.logging.logger import set_eo_gr_logger_for_class
from libs.common.constants import GR_TEST_PREFIX


class CvnfmNamespaceDeleter:
    """Class for deleting CVNFM namespaces from cluster"""

    def __init__(self, config: ConfigReader):
        self._config = config
        self._codeploy = CodeployApp(self._config)
        self.cluster_name = self._codeploy.env_name
        self.k8s_client = self._codeploy.k8s_eo_client
        self.logger = set_eo_gr_logger_for_class(self)
        self.asset_names = AssetNames()

    def delete_namespace_by_shared_name(self) -> None:
        """Delete namespace by provided shared name env variable"""

        namespace_name = self.asset_names.cnf_instance_name
        self.logger.info(
            f"Try to delete CNF {namespace_name!r} namespace from {self.cluster_name} if it exists..."
        )
        try:
            self.k8s_client.delete_namespace(namespace_name)
            self.logger.info(
                f"Namespace {namespace_name!r} deleted from {self.cluster_name!r} cluster"
            )
        except NamespaceNotFoundException:
            self.logger.info(
                f"Namespace {namespace_name!r} is not deleted "
                f"because it does not exists on {self.cluster_name!r} cluster"
            )

    def delete_namespaces_by_default_prefix(self) -> None:
        """Method that deleted CNF namespaces by default pattern from cluster"""

        self.logger.info(f"Deletion of namespaces that starts with {GR_TEST_PREFIX!r}")
        is_ns_deleted = False

        ns_names = self.k8s_client.get_list_namespaces()
        for ns_name in ns_names:
            if ns_name.startswith(GR_TEST_PREFIX):
                self.logger.info(
                    f"Deleting namespace {ns_name!r} from {self.cluster_name!r} cluster..."
                )
                # deleting some ns (e.g. with broken objects) may take longer than usual
                self.k8s_client.delete_namespace(ns_name, timeout=2 * 60)
                is_ns_deleted = True
                self.logger.info(
                    f"Namespace {ns_name!r} deleted from {self.cluster_name!r} cluster"
                )
        if not is_ns_deleted:
            self.logger.info(
                f"Namespaces that stars with {GR_TEST_PREFIX!r} "
                f"were not found on {self.cluster_name!r} cluster."
            )
