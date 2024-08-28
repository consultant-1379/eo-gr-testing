"""A module that stores PVs and PVCs cleaning up functionality"""
from functools import cached_property
from http import HTTPStatus

from core_libs.common.constants import CcdConfigKeys, CommonConfigKeys
from core_libs.common.custom_exceptions import (
    PvcNotFoundException,
    PersistentVolumeNotFoundException,
)
from core_libs.eo.ccd.k8s_api_client import K8sApiClient
from core_libs.vim.openstack import OpenStack
from kubernetes.client import ApiException, V1PersistentVolume

from libs.common.config_reader import ConfigReader
from libs.common.eo_rv_node.constants import EoNodePaths
from libs.common.eo_rv_node.eo_rv_node import EoRvNode
from libs.common.pv_cleaner.constants import CloudVolumeKeys, CloudVolumeStatuses
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class PersistentVolumeCleaner:
    """Provides functionality for the stuck PVs and PVCs removal"""

    def __init__(self, config: ConfigReader):
        self.config = config
        self._namespace = None
        self._logger = set_eo_gr_logger_for_class(self)
        self._k8s_client: K8sApiClient | None = None
        self.define_namespace()

    @property
    def namespace(self) -> str:
        """Receive namespace name for which persistent volume cleaning will be performed"""
        return self._namespace

    @cached_property
    def env_name(self) -> str:
        """ENV_NAME property"""
        return self.config.read_section(CommonConfigKeys.ENV_NAME)

    @property
    def k8s_client(self) -> K8sApiClient | None:
        """K8s client"""
        return self._k8s_client

    @cached_property
    def openstack(self) -> OpenStack:
        """OpenStack client"""
        return OpenStack(self.config, cluster_vim=True)

    @cached_property
    def eo_node(self) -> EoRvNode:
        """EoRvNode instance for interact with EO Node"""
        return EoRvNode(self.config)

    def define_namespace(self) -> None:
        """Define a namespace for which persistent volume cleaning will be performed
        Due to use same clusters for EO GR installation, and for EO LM installation in their own namespaces
        and clusters resources limitation simultaneous deploys are not possible,
        so there can be either EO GR namespace or EO LM namespace.
        """
        self._logger.info(
            "Define a namespace for which persistent volume cleaning will be performed"
        )
        config_ns = self.config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE)

        self._k8s_client = K8sApiClient(
            namespace=config_ns,
            kubeconfig_path=self.config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH),
        )
        list_ns = self._k8s_client.get_list_namespaces()

        if lm_ns := [n for n in list_ns if self.is_namespace_lm(n)]:
            lm_ns = lm_ns.pop()
            self._namespace = lm_ns

            if config_ns in list_ns:
                self._logger.warning(
                    f"There are both {lm_ns!r} and {config_ns!r} exist on the cluster! "
                    "This may cause EO installation problems."
                )
        else:
            self._namespace = config_ns
        self._k8s_client.namespace = self.namespace
        self._logger.info(f"Namespace was defined: {self.namespace!r}")

    def is_namespace_lm(self, namespace: str | None = None) -> bool:
        """Check if namespace is EO LM namespace
        Args:
            namespace: namespace name
        Returns:
            True if EO LM, False otherwise
        """
        return (namespace or self.namespace).startswith("lm-")

    def patch_and_remove_pv(self, body: V1PersistentVolume) -> None:
        """
        Patch and remove Persistent Volume instance
        Args:
            body: Modified V1PersistentVolume instance to patch and remove
        """
        body.metadata.finalizers = None
        try:
            self.k8s_client.patch_persistent_volume(body=body)
            self.k8s_client.delete_persistent_volume(name=body.metadata.name)
        except PersistentVolumeNotFoundException:
            self._logger.info(
                f"Persistent volume {body.metadata.name} wasn't found. "
                f"It has already been removed. Skipping it..."
            )

    def remove_persistent_volumes(self) -> None:
        """
        Removes existing persistent volumes on the cluster
        Raises:
            ApiException: when request fails with status code other than 404 and 409
        """
        for pv in self.k8s_client.get_persistent_volume_list():
            if pv.spec.claim_ref.namespace == self.namespace:
                try:
                    self.patch_and_remove_pv(body=pv)
                except ApiException as err:
                    if err.status == HTTPStatus.CONFLICT:
                        self._logger.info(
                            "Retry patching and removing after refreshing the PV object"
                        )
                        pv = self.k8s_client.read_persistent_volume(pv.metadata.name)
                        self.patch_and_remove_pv(body=pv)
                        self._logger.info(
                            "Conflicting PV has been successfully removed"
                        )
                    else:
                        raise ApiException from err

    def remove_persistent_volume_claims(self) -> None:
        """
        Removes existing persistent volume claims attached to the EO namespace
        """
        for pvc in self.k8s_client.get_persistent_volume_claim_list(self.namespace):
            pvc.metadata.finalizers = None
            try:
                self.k8s_client.patch_persistent_volume_claim(body=pvc)
                self.k8s_client.delete_persistent_volume_claim(name=pvc.metadata.name)
            except PvcNotFoundException:
                self._logger.info(
                    f"Persistent volume claim {pvc.metadata.name} wasn't found. "
                    f"It has already been removed. Skipping it..."
                )

    def detach_cloud_volumes(self) -> None:
        """
        Removes all remaining attached and failed volumes from the cluster VIM zone
        """
        volumes = self.openstack.volumes.list_volumes_by_namespace(self.namespace)
        unexpected_statuses = CloudVolumeStatuses.IN_USE, CloudVolumeStatuses.ERROR
        for volume in volumes:
            if volume.status in unexpected_statuses and volume.attachments:
                for attachment in volume.attachments:
                    server_id = attachment[CloudVolumeKeys.SERVER_ID]
                    server = self.openstack.servers.get_server(server_id)
                    self.openstack.volumes.detach_volume(server=server, volume=volume)

    def remove_namespace_pv_pvc_and_vim_volumes(self) -> None:
        """
        Clean up remaining:
            - The eo-deploy namespace
            - All available PVs, PVCs on the k8s cluster
            - All VIM zone volumes attached to the eo-deploy namespace
        """
        if self.namespace in self.k8s_client.get_list_namespaces():
            if self.is_namespace_lm():
                self._uninstall_flux_resources()
            self.k8s_client.delete_namespace(self.namespace, timeout=10 * 60)
        self.remove_persistent_volume_claims()
        self.remove_persistent_volumes()
        self.detach_cloud_volumes()

    def _uninstall_flux_resources(self) -> None:
        """Uninstall flux resources via flux tool on EO Node, required before deleting EO-LM namespace
        Raises:
            ValueError: when namespace is not EO LM namespace
            RuntimeError: when flux resources are not deleted correctly
        """
        if not self.is_namespace_lm():
            raise ValueError(
                f"Uninstalling flux resources not allowed for non EO LM namespace: {self.namespace}!"
            )
        self._logger.info(
            f"Deleting flux resources for {self.namespace!r} EO-LM namespace..."
        )
        cluster_name = {"ci476": "c15a7", "ci480": "c11a3"}.get(
            self.env_name, self.env_name
        )
        kube_config = EoNodePaths.LM_WORK_DIR_KUBE_CONFIG.format(env_name=cluster_name)
        flux_uninstall_cmd = (
            f"flux uninstall -n {self.namespace} --kubeconfig {kube_config} -s"
        )
        output = self.eo_node.execute_cmd(cmd=flux_uninstall_cmd)
        if "uninstall finished" not in output:
            raise RuntimeError(f"flux resources are not deleted correctly: {output=}")
