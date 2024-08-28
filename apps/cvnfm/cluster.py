""" Module with Cluster class"""

import os

from apps.cvnfm.cvnfm_app import CvnfmApp
from libs.utils.logging.logger import logger


class Cluster(CvnfmApp):
    """
    Cluster class contains all methods related to Cluster
    """

    def __init__(self, config):
        super().__init__(config)
        self.cluster_config_path = None

    @property
    def cluster_name(self):
        """
        Retrieves the name of the cluster config
        :return: name of the cluster config
        :rtype: str or None
        """
        if self.cluster_config_path is not None:
            return os.path.basename(self.cluster_config_path)
        return self.cluster_config_path

    def register_cluster_config(self):
        """
        Registers new cluster config
        """
        logger.info("Register cluster config")
        with open(self.cluster_config_path, "rb") as f:
            self.api.clusters.register_cluster_config(
                self.evnfm_test_data.cluster_test_data.register_cluster_data(f)
            )
            logger.info("Kubernetes cluster config registration succeeded")

    def deregister_cluster_config(self):
        """
        Deletes registered cluster
        """
        logger.info("Delete registered cluster")
        if self.is_cluster_config_registered():
            self.api.clusters.delete_cluster_config(self.cluster_name)
            logger.info("Kubernetes cluster config de-registration succeeded")
        logger.info(f"No registered cluster with name {self.cluster_name} was found")

    def is_cluster_config_registered(self):
        """
        Check if cluster registered on system
        :return: if cluster config is registered
        :rtype: bool
        """
        logger.info("Check if cluster config registered")
        return self.api.clusters_client.check_for_cluster_config(self.cluster_name)
