"""Module to store Deployment Manager related constants"""

from libs.common.env_variables import ENV_VARS


class DmLogLevel:
    """
    Class that defines Deployment Manager Log level
    """

    DM_LOG_LEVELS = {
        "CRITICAL": 0,
        "ERROR": 1,
        "WARNING": 2,
        "INFO": 3,
        "DEBUG": 4,
    }  # Deployment Manager log levels that are taken from oos-deployment-manager repo

    LOG_LEVEL = DM_LOG_LEVELS.get(ENV_VARS.dm_log_level, 3)


class DeploymentManagerDockerCmds:
    """
    Class that contains commands for Deployment Manager docker operations
    """

    DM_DOCKER_CMD = (
        "docker run --rm -u $(id -u):$(id -g) "
        "-v {HOST_LOCAL_PWD}:/workdir "
        "-v /etc/hosts:/etc/hosts "
        "-v /var/run/docker.sock:/var/run/docker.sock "
        "{DM_IMG_NAME} {DM_CMD} "
        f"-v {DmLogLevel.LOG_LEVEL}"
    )

    DM_DOCKER_CMD_RV = (
        "cd /eo/workdir/workdir_{ENV_NAME} && "
        "docker run --rm -u $(id -u):$(id -g) "
        "{DNS_FLAG} "
        "-v $PWD:/workdir "
        "-v /etc/hosts:/etc/hosts "
        "-v /var/run/docker.sock:/var/run/docker.sock "
        "deployment-manager:{DM_VERSION} {DM_CMD} "
        f"-v {DmLogLevel.LOG_LEVEL}"
    )


class DeploymentManagerCmds:
    """
    Deployment Manager command constants
    """

    SWITCH_OVER_CMD = (
        "geo switchover --new-primary={new_primary} --new-secondary={new_secondary}"
    )
    SWITCH_OVER_WITH_BACKUP_ID_CMD = SWITCH_OVER_CMD + " --backup-id={backup_id}"
    GEO_STATUS_CMD = "geo status"
    GEO_AVAILABILITY = (
        "geo availability  --new-primary={primary} --new-secondary={secondary}"
    )
    COLLECT_LOGS = "collect-logs -n {namespace}"
    GEO_RECOVERY_STATUS = "geo recovery-status --recover-site {recover_site}"
    GEO_UPDATE_RECOVERY_STATE = (
        "geo update-recovery-state --recover-site {recover_site}"
    )


class DeploymentManagerPatterns:
    """Stores DM regex patterns"""

    ARCHIVE_LOG = r"Generated file s*(.*tgz)"
    CMD_EXECUTION_LOG = r"Logging to logs/s*(.*log)"
    DM_VERSION = r"deployment-manager-(\d*\.\d*\.\d*).zip"
