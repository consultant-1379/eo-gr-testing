"""Module contains constants and data related to GR BUR SFTP server"""
from pathlib import Path

from core_libs.eo.ccd.k8s_data.pod_model import K8sPod


class SftpServerConstants:
    """
    Stores constants related to BUR SFTP
    """

    DEPLOYMENT_NAME = "bur-sftp-dced"
    SERVICE_NAME = "bur-sftp-dced-svc"
    CONTAINER_NAME = "sftp-server"


SFTP_SERVER_POD = K8sPod(
    name=SftpServerConstants.DEPLOYMENT_NAME,
    container=SftpServerConstants.CONTAINER_NAME,
)


class BurSftpPaths:
    """
    Class to store BUR SFTP server paths to deployment files
    """

    SERVICE_CONF_FILE = Path(
        "resources/bur-sftp-deployment-data/bur-sftp-svc_backup-modified.yaml"
    )
    DEPLOYMENT_CONF_FILE = Path(
        "resources/bur-sftp-deployment-data/bur-sftp_deployment_backup-modified.yaml"
    )
