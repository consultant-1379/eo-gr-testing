"""
Contains a script that:
   Verifies if Storage Class network file-system for VMVNFM HA feature is mounted to the cluster, if not, it will mount.
   It's part of cluster post-installation activities.
"""

from core_libs.common.custom_exceptions import StorageClassNotFoundException

from apps.codeploy.codeploy_app import CodeployApp
from apps.codeploy.master_node import MasterNode
from libs.common.constants import GrEnvVariables
from util_scripts.common.common import print_with_highlight
from util_scripts.common.config_reader import active_site_config

STORAGE_CLASS_NAME = "network-file"
NAMESPACE = "kube-system"
NFS_NAME = "nfs-fs3"
NFS_SERVER_IP = "10.232.14.23"

if __name__ == "__main__":
    print_with_highlight(
        f"""
        Script verifies if Storage Class {STORAGE_CLASS_NAME!r} for VMVNFM HA feature is mounted to the cluster,
        if not, it will mount.
        Required environment variables:
            - {GrEnvVariables.ACTIVE_SITE}
        """
    )
    print_with_highlight("Script is running....")

    # getting IP address of any master node after cluster re-install directly from cluster's VIM,
    # due to IP from config is outdated
    codeploy_app = CodeployApp(active_site_config)
    master_node_ip = codeploy_app.collect_master_nodes_ips()[0]
    master_node = MasterNode(config=active_site_config, ip=master_node_ip)

    if not master_node.is_nfs_deployment_exists(NFS_NAME, NAMESPACE):
        # delete existing SC if it has required name to prevent installation conflict
        codeploy_app.k8s_eo_client.delete_storage_class(
            name=STORAGE_CLASS_NAME, raise_exc=False
        )

        master_node.add_nfs_repo()
        master_node.install_nfs(
            nfs_name=NFS_NAME,
            namespace=NAMESPACE,
            nfs_server_ip=NFS_SERVER_IP,
            storage_class_name=STORAGE_CLASS_NAME,
        )

        if not master_node.is_nfs_deployment_exists(NFS_NAME, NAMESPACE):
            raise RuntimeError(
                f"Something went wrong...{NFS_NAME!r} nfs storage class is not installed!"
            )
        if not codeploy_app.k8s_eo_client.is_storage_class_exists(STORAGE_CLASS_NAME):
            raise StorageClassNotFoundException(
                f"{STORAGE_CLASS_NAME!r} is not created after installing NFS!"
            )

        print_with_highlight(
            f"{STORAGE_CLASS_NAME!r} storage class has been mounted to the {master_node.cluster_name!r} cluster."
        )
    else:
        print_with_highlight(
            f"{STORAGE_CLASS_NAME!r} storage class has been already mounted "
            f"to the {master_node.cluster_name!r} cluster. Skipped installation procedures."
        )
