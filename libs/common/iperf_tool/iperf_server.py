"""A module to store IperfToolServer class"""

from functools import cached_property

from core_libs.common.constants import CcdConfigKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient

from libs.common.config_reader import ConfigReader
from libs.common.iperf_tool.constants import IperfServerPaths
from libs.utils.logging.logger import set_eo_gr_logger_for_class


class IperfToolServer:
    """A class to create iperf3 tool as a server"""

    def __init__(self, config: ConfigReader):
        self._config = config
        self.namespace = "gr-iperf"
        self.service_name = "gr-iperf-svc"
        self.server_pod = "gr-iperf-server"
        self._logger = set_eo_gr_logger_for_class(self)

    def __enter__(self) -> "IperfToolServer":
        """Enter method to use as contextmanager"""
        self.create_server_as_pod()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit from contextmanager"""
        self.delete_server()

    @cached_property
    def _k8s_client(self) -> K8sApiClient:
        """K8s client
        Returns:
            K8s client
        """
        return K8sApiClient(
            namespace=self.namespace,
            kubeconfig_path=self._config.read_section(
                CcdConfigKeys.CCD_KUBECONFIG_PATH
            ),
        )

    def create_server_as_pod(self) -> None:
        """Create Iperf3 server pod"""
        self._delete_k8s_namespace()
        self._k8s_client.create_namespace(self.namespace)

        self._logger.info(f"Create {self.service_name} k8s service")
        self._k8s_client.create_service_from_yaml(
            yaml_file=IperfServerPaths.SERVICE_CONFIG
        )
        self._logger.info(f"Create {self.server_pod!r} pod with iperf3 server")
        self._k8s_client.create_k8s_obj_from_yaml(
            yaml_file=IperfServerPaths.SERVER_POD_CONFIG
        )
        self._k8s_client.wait_till_pod_up(pod_full_name=self.server_pod)
        self._logger.info(
            f"Iperf3 server has been created as k8s pod: {self.server_pod} in {self.namespace} ns"
        )

    def delete_server(self) -> None:
        """Delete iperf server pod and other k8s related objects"""
        self._logger.info("Delete Iperf server pod and other k8s related objects")
        self._delete_k8s_namespace()

    @property
    def server_load_balancer_ip(self) -> str:
        """Receive LoadBalancer IP from iperf service
        Returns:
            LoadBalancer IP
        """
        return self._k8s_client.get_service_load_balancer_ip(self.service_name)

    def _delete_k8s_namespace(self) -> None:
        """Delete namespace where iperf3 server located"""
        self._logger.info(f"Try to delete  {self.namespace} namespace")
        self._k8s_client.delete_namespace(self.namespace, raise_exc=False)
