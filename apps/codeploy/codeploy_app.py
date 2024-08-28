""" Module with CodeployApp class"""
import asyncio
import subprocess
from functools import cached_property

from core_libs.common.console_commands import CMD
from core_libs.common.constants import CcdConfigKeys, CommonConfigKeys
from core_libs.common.custom_exceptions import PodNotFoundException
from core_libs.common.decorators import retry_deco
from core_libs.common.misc_utils import (
    decode_base64,
    get_server_cert,
    wait_for,
)
from core_libs.eo.ccd.constants import ConfigMapKeys
from core_libs.eo.ccd.k8s_api_client import K8sApiClient
from core_libs.eo.ccd.k8s_data.configmaps import CcdConfigmaps
from core_libs.eo.ccd.k8s_data.pod_data import K8sSearchWords
from core_libs.eo.ccd.k8s_data.pod_model import K8sPod
from core_libs.eo.ccd.k8s_data.pods import (
    ERIC_CTRL_BRO,
    ERIC_GR_BUR_ORCH,
    ERIC_VNFLCM_DB,
    IDAM_DB_PG,
)
from core_libs.eo.ccd.k8s_data.secrets import CcdSecrets
from core_libs.eo.integration.integration_data import CvnfmIntegrationData
from core_libs.vim.data.constants import ServerKeys
from core_libs.vim.openstack import OpenStack
from kubernetes.client import V1Deployment

from apps.codeploy.data.cluster_data import (
    ClusterSecrets,
    get_snmp_alarm_provider_secrets_data,
)
from apps.codeploy.data.constants import CodeployDetails, HAPods
from apps.codeploy.master_node import MasterNode
from apps.gr.data.constants import SwitchoverPods, GrTimeouts
from libs.common.config_reader import ConfigReader
from libs.common.constants import DEFAULT_DOWNLOAD_LOCATION, EoApps
from libs.common.custom_exceptions import (
    DockerRegistryAvailabilityError,
    MissingKeyInConfigMapError,
    MasterNodeNotFoundError,
)
from libs.common.deployment_manager.dm_collect_logs import (
    DeploymentManagerLogCollection,
)
from libs.common.master_node_ssh_client import SSHMasterNode
from libs.common.versions_collector import VersionCollector
from libs.utils.common_utils import is_asyncio_task_alive, compare_versions
from libs.utils.logging.logger import logger, log_exception


class CodeployApp:
    """
    CodeployApp class contains all apps deployed as codeploy and all methods related to these apps
    integration
    """

    def __init__(self, config: ConfigReader):
        self.config = config
        self._k8s_eo_client = None

    @cached_property
    def k8s_eo_client(self) -> K8sApiClient:
        """
        K8s EO client property
        :return: instance of K8sApiClient class
        :rtype: K8sApiClient
        """
        return K8sApiClient(
            namespace=self.namespace,
            kubeconfig_path=self.kubeconfig_path,
            download_location=DEFAULT_DOWNLOAD_LOCATION,
        )

    @cached_property
    def dm_log_collector(self) -> DeploymentManagerLogCollection:
        """
        DM Log Collection property
        Returns:
            DeploymentManagerLogCollection instance
        """
        return DeploymentManagerLogCollection(self.config)

    @property
    def env_name(self) -> str:
        """Environment name"""
        return self.config.read_section(CommonConfigKeys.ENV_NAME)

    @property
    def namespace(self) -> str:
        """EO namespace property"""
        return self.config.read_section(CcdConfigKeys.CODEPLOY_NAMESPACE)

    @property
    def kubeconfig_path(self) -> str:
        """A kubeconfig path property"""
        return self.config.read_section(CcdConfigKeys.CCD_KUBECONFIG_PATH)

    @property
    def docker_registry_host(self) -> str:
        """A docker_registry_host property"""
        return self.config.read_section(CcdConfigKeys.DOCKER_REGISTRY_HOST)

    @property
    def global_registry_host(self) -> str:
        """A global_registry_host property"""
        return self.config.read_section(CcdConfigKeys.GLOBAL_REGISTRY_HOST)

    @property
    def helm_registry_host(self) -> str:
        """A helm_registry_host property"""
        return self.config.read_section(CcdConfigKeys.HELM_REGISTRY_HOST)

    @property
    def iccr_ip(self) -> str:
        """The ICCR IP property"""
        return self.config.read_section(CcdConfigKeys.ICCR_IP)

    @property
    def ro_snmp_ip(self) -> str:
        """The RO SNMP IP property"""
        return self.config.read_section(CcdConfigKeys.RO_SNMP_IP)

    @cached_property
    def version_collector(self) -> VersionCollector:
        """VersionCollector instance for getting EO components versions"""
        return VersionCollector(k8s_eo_client=self.k8s_eo_client)

    @cached_property
    def master_node(self) -> MasterNode:
        """MasterNode instance for interact with EO Master Node
        Returns:
            MasterNode instance
        """
        return MasterNode(config=self.config)

    @cached_property
    def openstack_cluster(self) -> OpenStack:
        """Openstack cluster object
        Returns:
            Openstack cluster object
        """
        return OpenStack(config=self.config, cluster_vim=True)

    @cached_property
    def is_vmvnfm_installed(self) -> bool:
        """
        Verifies whether the VMVNFM is included into the actual EO installation on the active site or not
        Returns:
            A boolean value: True if VMVNFM is installed, False otherwise
        """
        vmvnfm_version = self.version_collector.get_version(app_name=EoApps.VMVNFM)
        return vmvnfm_version == self.version_collector.not_installed

    def connect_master_node(
        self, *, worker_ip: str | None = None, worker_username: str | None = None
    ) -> SSHMasterNode:
        """
        Establishes an SSH connection to the EO Master node
        Args:
            worker_ip: IP address of the worker node
            worker_username: Worker node username
        Returns:
            An instance of the SSHMasterNode class
        """
        logger.info(f"Connect to EO master node: {self.master_node.ip} via SSH")
        return self.master_node.set_ssh_client(
            worker_ip=worker_ip, worker_username=worker_username
        )

    def get_secrets_values(self) -> dict:
        """
        Get cluster secrets values
        :return: secrets values
        """
        logger.info("Get cluster secrets values")
        secrets_values = {}
        for element in (
            ClusterSecrets.HELM_CHART_REGISTRY,
            ClusterSecrets.DOCKER_REGISTRY,
        ):
            secret_data = self.k8s_eo_client.get_secret(
                element[CodeployDetails.NAME]
            ).data
            el_data = element[CodeployDetails.DATA]
            for k, v in el_data.items():
                el_data[k] = decode_base64(secret_data[v]).replace("https://", "")
            secrets_values = {**secrets_values, **el_data}
        secrets_values = CvnfmIntegrationData.get_secret_values_for_abcd(
            **secrets_values
        )
        return secrets_values

    def get_docker_registry_tls_cert_data(self, decode: bool = True) -> str:
        """
        Method to get the Docker registry TLS certificate
        :param decode: Decode the output with base64
        :raise KeyError: if DATA_TLS_SRT key is not found
        :return: Docker registry TLS certificate
        """
        logger.info("Get Docker registry certificate data")
        try:
            crt = self.k8s_eo_client.get_secret(
                CodeployDetails.DOCKER_REGISTRY_TLS_SECRET
            ).data[CodeployDetails.DATA_TLS_SRT]
            if decode:
                return decode_base64(crt)
            return crt
        except KeyError as err:
            raise KeyError(
                logger.error(
                    f'The key "{CodeployDetails.DATA_TLS_SRT}" is absent in the secret '
                    f'"{CodeployDetails.DOCKER_REGISTRY_TLS_SECRET}" data.'
                )
            ) from err

    def get_helm_registry_tls_cert_data(self, decode: bool = True) -> str:
        """
        Method to get Helm registry TLS certificate
        :param decode: Decode the output with base64
        :raise KeyError: if DATA_TLS_SRT key is not found
        :return: Helm registry TLS certificate
        """
        logger.info("Get Helm registry certificate data")
        try:
            crt = self.k8s_eo_client.get_secret(
                CodeployDetails.HELM_REGISTRY_TLS_SECRET
            ).data[CodeployDetails.DATA_TLS_SRT]
            if decode:
                return decode_base64(crt)
            return crt
        except KeyError as err:
            raise KeyError(
                logger.error(
                    f'The key "{CodeployDetails.DATA_TLS_SRT}" is absent in the secret '
                    f'"{CodeployDetails.HELM_REGISTRY_TLS_SECRET}" data.'
                )
            ) from err

    def create_evnfm_nfvo_secret(
        self, eocm_hostname: str, user: str, password: str, tenant: str
    ) -> None:
        r"""
        Creates 'eric-eo-evnfm-nfvo' secret for EOCM + CVNFM integration
        :param eocm_hostname: EOCM hostname
        :param user: EOCM username
        :param password: EOCM password
        :param tenant: EOCM tenant
        """
        logger.info('Create "eric-eo-evnfm-nfvo" secret')
        data = CvnfmIntegrationData.get_secret_for_evnfm_nfvo(
            user=user,
            password=password,
            tenant=tenant,
            tls=get_server_cert(eocm_hostname),
        )
        self.k8s_eo_client.create_secret(
            name=CodeployDetails.EOCM_SECRET_NAME, data=data
        )

    @staticmethod
    def is_docker_registry_available(
        docker_registry_host: str, user_name: str, password: str
    ) -> bool:
        """
        Method to check if docker registry available
        Args:
            docker_registry_host: host for which check should be done
            user_name: username for login operation
            password: password for login operation
        Return:
             True if login success else False
        """
        cmd = f"docker login {docker_registry_host} -u {user_name} -p {password}"
        with subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            text=True,
        ) as proc:
            stdout = proc.stdout.read()
            stderr = proc.stderr.read()
            command_to_be_executed = " ".join(cmd.split()[:-1]) + " *****"
            logger.info(
                f"Login to docker registry {docker_registry_host=} to check if it available via command:\n"
                f"{command_to_be_executed}"
            )
            if stdout:
                logger.info(f"STDOUT output: {stdout}")
                return "Login Succeeded" in stdout
            logger.error(f"Failed with error: {stderr}")
            return False

    def verify_local_and_global_registries_availability(
        self, registry_username: str, registry_user_password: str
    ) -> None:
        """
        Verify docker global and local registries
        Args:
            registry_username: docker registry username
            registry_user_password: docker registry user password
        Raises:
            DockerRegistryAvailabilityError: when docker registry not available
        """
        logger.info("Verify that docker global and local registries are available")
        is_global_reg_available = self.is_docker_registry_available(
            docker_registry_host=self.global_registry_host,
            user_name=registry_username,
            password=registry_user_password,
        )
        is_local_reg_available = self.is_docker_registry_available(
            docker_registry_host=self.docker_registry_host,
            user_name=registry_username,
            password=registry_user_password,
        )
        if not is_global_reg_available or not is_local_reg_available:
            raise DockerRegistryAvailabilityError(
                log_exception(
                    f"Docker Registry Unavailable: "
                    f"Global registry {self.global_registry_host=} availability is {is_global_reg_available!r} "
                    f"Local registry {self.docker_registry_host=} availability is {is_local_reg_available!r}"
                )
            )
        logger.info("Docker global and local registries availability check completed")

    def change_deployment_replicas(self, pod: K8sPod, replicas: int) -> None:
        """
        Change number of replicas for deployment

        Args:
            pod: K8sPod instance for witch replicas should be changed
            replicas: number of replicas
        """
        logger.info(f"Change {pod.name} deployment replicas to {replicas}")
        self.k8s_eo_client.scale_deployment_replicas(pod, replicas)

    def change_stateful_set_replicas(
        self, pod: K8sPod, replicas: int, timeout: int = 200
    ) -> None:
        """
        Change number of replicas for stateful set pod

        Args:
            pod: K8sPod instance for witch replicas should be changed
            replicas: number of replicas
            timeout: time to wait until pod readiness
        """
        logger.info(f"Change {pod.name} stateful set replicas to {replicas}")
        self.k8s_eo_client.scale_stateful_set_replicas(pod, replicas, timeout=timeout)

    async def restart_bur_pod_when_gr_pods_ready_async(self, task_name: str) -> None:
        """
        Method that restarts bur-orchestrator pod when GR pods are ready on passive site
        while async switchover task running (still alive)
        Args:
            task_name: asyncio switchover task name
        """
        logger.info(
            f"Start to wait condition for restart {ERIC_GR_BUR_ORCH.name!r} pod"
        )
        for pod in SwitchoverPods.HEALTH_CHECK_LIST_CVNFM:
            while not self.k8s_eo_client.is_pod_exists(pod) and is_asyncio_task_alive(
                task_name=task_name
            ):
                await asyncio.sleep(5)

        self.k8s_eo_client.delete_pod(pod=ERIC_GR_BUR_ORCH)

    async def restart_bro_pod_when_db_pod_starts_to_recreate_async(
        self, task_name: str
    ) -> None:
        """
        Method that restarts ctrl-bro pod on passive site when vnflcm-db pod starts to recreate
        on passive site while async switchover task running (still alive)
        Args:
            task_name: asyncio switchover task name
        """
        logger.info(f"Start to wait condition for restart {ERIC_CTRL_BRO.name!r} pod")
        while self.k8s_eo_client.is_pod_running(
            pod=ERIC_VNFLCM_DB
        ) and is_asyncio_task_alive(task_name=task_name):
            await asyncio.sleep(5)

        self.k8s_eo_client.delete_pod(pod=ERIC_CTRL_BRO)

    def pods_health_check(
        self,
        *,
        should_pods_exists: bool,
    ) -> str:
        """
        Method that check pods health check.
        Args:
            should_pods_exists: to check if pods exists on not. True if pods should exist else False
        Returns:
            list of unhealthy pods
        """
        logger.info(f"Make a health check of pods on site: {self.env_name}")
        health_check_msg = ""
        unhealthy_pods_names = []
        pods_check_list = (
            SwitchoverPods.HEALTH_CHECK_LIST_CVNFM
            if not self.is_vmvnfm_installed
            else SwitchoverPods.COMPLETE_HEALTH_CHECK_LIST
        )
        for pod in pods_check_list:
            if self.is_vmvnfm_installed and self.is_pod_ha_enabled(pod):
                try:
                    pods = self.k8s_eo_client.get_pods_full_names(pod)
                except PodNotFoundException:
                    pods = []
                expected_pods = HAPods.NUMBER_HA_PODS if should_pods_exists else 0

                if len(pods) != expected_pods:
                    for pod_name in pods:
                        pod_details = self.k8s_eo_client.get_pod(pod_full_name=pod_name)
                        if not self.k8s_eo_client.is_pod_terminated(pod_details):
                            unhealthy_pods_names.append(
                                f"{pod.name}: expected: {expected_pods} / actual: {pods}]"
                            )
            else:
                is_pod_exists = self.k8s_eo_client.is_pod_exists(pod)
                if should_pods_exists is not is_pod_exists:
                    if not is_pod_exists or not self.k8s_eo_client.is_pod_terminated(
                        pod
                    ):
                        unhealthy_pods_names.append(pod.name)
        if unhealthy_pods_names:
            logger.warning(
                f"Unhealthy pods on site {self.env_name} found: {unhealthy_pods_names}"
            )
            health_check_msg = (
                f"\nPods healthcheck on site {self.env_name!r} failed. "
                f"Failed pods are: {unhealthy_pods_names} "
                f"Those pods should {'' if should_pods_exists else 'not '}be present."
            )
        else:
            logger.info(
                f"Pods health check on site {self.env_name} successfully finished."
            )
        return health_check_msg

    def wait_and_get_failed_pods(self) -> list:
        """It's a wrapper under get_failed_pod that applies GR Controller pod up state timeout
        for checking pod status after switchover operation.
        Returns:
            list of failed pod if found, empty list otherwise
        """
        logger.debug(
            f"Start waiting {GrTimeouts.GR_CONTROLLER_POD_UP_STATE} sec. for pods up according to GR Controller."
        )
        failed_pods = []

        def get_failed_pods() -> list:
            """Get failed pods
            Returns:
                list of failed pod if found, empty list otherwise
            """
            nonlocal failed_pods
            failed_pods = self.k8s_eo_client.get_failed_pods(
                exclude_terminated_pods=True
            )
            logger.debug(
                f"Failed pods found: {[p.metadata.name for p in failed_pods]}."
                if failed_pods
                else "No failed pods found."
            )
            return failed_pods

        result = wait_for(
            lambda: len(get_failed_pods()) == 0,
            interval=15.0,
            timeout=GrTimeouts.GR_CONTROLLER_POD_UP_STATE,
            raise_exc=False,
        )
        if not result:
            logger.error(
                f"GR Controller timeout {GrTimeouts.GR_CONTROLLER_POD_UP_STATE} exited. Some pods are not up."
            )
        return failed_pods

    def failed_pods_check(self) -> str:
        """
        Method that returns failed pods info string
        Returns:
            string with failed pods formatted as string
        """
        logger.info(f"Get failed pods on {self.env_name!r}")
        failed_pods_msg = ""
        failed_pods = self.wait_and_get_failed_pods()

        for pod in failed_pods:
            pod_name = pod.metadata.name
            pod_state = pod.status.phase
            num_of_pod_ctrs = len(pod.status.container_statuses)
            num_of_failed_ctrs = len(
                self.k8s_eo_client.get_not_ready_pod_containers(pod)
            )
            container_status = (
                f"{num_of_pod_ctrs - num_of_failed_ctrs}/{num_of_pod_ctrs}"
            )
            failed_pods_msg += f"{pod_name: <70} \t{pod_state} \t{container_status}\n"

        if failed_pods_msg:
            failed_pods_msg = (
                f"Found failed pods on site {self.env_name!r}.\n"
                f"Failed pods are: {failed_pods_msg}"
            )
            logger.warning(failed_pods_msg)
        else:
            logger.info(f"No failed pods on site {self.env_name} found.")
        return failed_pods_msg

    def is_pod_ha_enabled(self, pod: K8sPod) -> bool:
        """Check if pod supports HA and HA is enabled for it
        Args:
            pod: pod object
        Returns:
            True if pod supports HA and HA is enabled for it otherwise False
        """
        if pod in HAPods.HA_PODS_LIST:
            pod_name = pod.name
            if pod.sts_name:
                pod_name = self.k8s_eo_client.get_stateful_set_name(pod)
            if K8sSearchWords.HA in pod_name:
                logger.debug(f"HA is enabled for {pod_name!r} pod")
                return True
        return False

    def update_bur_orchestrator_deployment_env_variable(
        self, env_var: str, value: str | int
    ) -> V1Deployment:
        """
        Patch bur orchestrator deployment environment variable with provided value
        Args:
            env_var: bur orchestrator deployment env variable
            value: desired value
        Raises:
            ValueError: when provided env var is missing in deployment
        Returns:
            Patched deployment object
        """
        logger.info(
            f"Updating {ERIC_GR_BUR_ORCH.name!r} deployment with {env_var}:{value} ..."
        )
        deployment = self.k8s_eo_client.read_deployment(ERIC_GR_BUR_ORCH.name)
        for var in deployment.spec.template.spec.containers[0].env:
            if var.name == env_var:
                if var.value != value:
                    var.value = value

                    return self.k8s_eo_client.patch_and_check_deployment(
                        pod=ERIC_GR_BUR_ORCH, deployment=deployment, timeout=180
                    )
                logger.warning(
                    f"Skip update.{ERIC_GR_BUR_ORCH.name!r} deployment has already updated to {env_var}:{value} !"
                )
                return deployment
        raise ValueError(
            f"{env_var!r} env variable is not found in {ERIC_GR_BUR_ORCH.name!r} deployment"
        )

    def check_free_memory_on_pod(self, pod: K8sPod, file_sys_name: str) -> str:
        """
        Checks a free memory space on the BRO pod
        Args:
            pod: K8sPod instance
            file_sys_name: The name of the file system to check
        Returns:
            Amount of a free memory space
        """
        return self.k8s_eo_client.exec_in_pod(
            pod=pod,
            cmd=CMD.DF_FREE_SPACE.format(file_system=file_sys_name),
        ).strip()

    def generate_file_of_size_on_pod(
        self, pod: K8sPod, file_size: str, file_path: str
    ) -> None:
        """
        Generates a file of the specific size on a pod
        Args:
            pod: K8sPod instance
            file_size: A size of a file to generate
            file_path: A path for the generated file
        """
        logger.info(f"Generating a large file to fill up {file_size} on {pod.name} pod")
        create_file_cmd = CMD.CREATE_FILE_OF_SIZE.format(
            file_size=file_size, file_path=file_path
        )
        self.k8s_eo_client.exec_in_pod(pod=pod, cmd=create_file_cmd)

    def fill_up_free_memory_on_pod(
        self, pod: K8sPod, file_sys_name: str, file_path: str, timeout: int = 20
    ) -> None:
        """
        Fills up all free memory space on the pod by creating a large file
        Args:
            pod: K8sPod instance
            file_sys_name: A file system name of the pod
            file_path: A path for the generated file
            timeout: Timeout for creating a large file on the pod
        Raises:
            TimeoutError: when waiting time is over
        """
        logger.info(f"Verifying a size of the free memory on the {pod.name} pod")
        free_memory = self.check_free_memory_on_pod(pod, file_sys_name)

        self.generate_file_of_size_on_pod(pod, free_memory, file_path)
        logger.info(
            f"Verifying that no free memory space is available on the {pod.name} pod"
        )
        wait_for(
            lambda: self.check_free_memory_on_pod(pod, file_sys_name) == "0",
            timeout=timeout,
            exc_msg=f"{pod.name} pod still has {self.check_free_memory_on_pod(pod, file_sys_name)} of free memory",
        )

    @retry_deco(MissingKeyInConfigMapError)
    def get_idam_db_pod_leader_name(self) -> str:
        """Get pod name with leader role for idam DB
        NOTE: the 'leader' key may disappear for a short time after killing leader pod
        Raises:
            MissingKeyInConfigMapError: when the 'leader' key is missing in configmap
        Returns:
            db leader pod name
        """
        logger.info(f"Getting {IDAM_DB_PG.name!r} pod leader name...")
        cm_data = self.k8s_eo_client.get_configmap(CcdConfigmaps.IDAM_DB_PG_LEADER)
        try:
            idam_db_leader = cm_data.metadata.annotations[ConfigMapKeys.LEADER]
        except KeyError as exc:
            raise MissingKeyInConfigMapError(
                f"{ConfigMapKeys.LEADER!r} key is missing in {CcdConfigmaps.IDAM_DB_PG_LEADER!r} configmap"
            ) from exc

        logger.info(f"{idam_db_leader=}")
        return idam_db_leader

    def create_alarm_secret(self) -> None:
        """
        Create secret for enabling the ability to send alarm data to an external system through SNMP
        """
        logger.info(
            f"Create {CcdSecrets.SNMP_ALARM_PROVIDER_CONFIG!r} secret for {self.env_name!r} cluster"
        )
        secret_data = get_snmp_alarm_provider_secrets_data(self.ro_snmp_ip)

        self.k8s_eo_client.create_secret(
            name=CcdSecrets.SNMP_ALARM_PROVIDER_CONFIG, data=secret_data
        )

    def compare_eo_version(self, target_version: str, comparator: str = ">=") -> bool:
        """Compare current EO version with target version
        Args:
            target_version: a target version to be compared with
            comparator: one of possible relational operators (>,<,>=,<=,==,!=)
        Returns:
            a result of the relational comparison
        """
        eo_version = self.version_collector.eo_version
        result = compare_versions(
            current_version=eo_version,
            comparator=comparator,
            target_version=target_version,
        )
        logger.info(
            f"Result of comparison {eo_version=} {comparator} {target_version=} -> {result}"
        )
        return result

    def collect_master_nodes_ips(self) -> list:
        """Collection Master Nodes IPs from cluster's VIM
        Raises:
            MasterNodeNotFoundError: when there is no master node found
        Returns:
            list with IPs
        """
        logger.info(f"Collecting Master Nodes IPs from {self.env_name!r} cluster's VIM")
        master_nodes = [
            server
            for server in self.openstack_cluster.servers.list_servers()
            if server[ServerKeys.NAME].startswith(f"{self.env_name}-cp-")
            or f"{self.env_name}-controlplane-" in server[ServerKeys.NAME]
        ]
        if not master_nodes:
            raise MasterNodeNotFoundError(
                f"Master nodes are not found on {self.env_name!r} cluster's VIM"
            )
        ips = [master[ServerKeys.IPV4] for master in master_nodes]
        logger.info(f"Master Nodes IPs: {ips}")

        return ips
