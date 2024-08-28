"""
Module that contains relative Geographical Redundancy constants
"""
import re

from core_libs.eo.ccd.k8s_data.pods import (
    COMMON_WFS,
    VNFLCM_SERVICE,
    EVNFM_NBI,
    VNFM_ORCHESTRATOR_SERVICE,
    EO_AM_ONBOARDING,
    ERIC_EO_EVNFM_CRYPTO,
    ERIC_EO_LM_CONSUMER,
    ERIC_EO_USERMGMT,
    EVNFM_TOSCAO,
)


class GrStatusKeys:
    """
    Class to store GR Status output keys
    """

    ACTIVE_APP = "Active Applications"
    LAST_EXP_BACKUP = "Last Exported Backup"
    LAST_IMP_BACKUP = "Last Imported Backup"
    CLUSTER_VERSION = "Cluster Version of EO"
    IMAGE_SYNC = "Last Successful Image Synchronisation"
    HOST_MATCH = "Primary GR Host matches DNS Entry"
    PRIMARY_DETAILS = "Primary Details"
    SECONDARY_DETAILS = "Secondary Details"


class GrSearchPatterns:
    """
    GR search regex patterns
    """

    # Geo Status
    PRIMARY_DETAILS = (
        re.escape(GrStatusKeys.PRIMARY_DETAILS)
        + r"(.*)"
        + re.escape(GrStatusKeys.SECONDARY_DETAILS)
    )
    SECONDARY_DETAILS = re.escape(GrStatusKeys.SECONDARY_DETAILS) + r"(.*)"
    BY_KEY = r"{}\s*:\s*(.*)"

    # Geo Availability
    AVAILABILITY_AVAILABLE = r"Availability.*:\sAvailable"

    # Switchover
    SWITCH_OVER_SUCCESS_STATUS = r"Switchover\sStatus.*:\sSUCCESS"
    SWITCH_OVER_FAILURE_STATUS = r"Switchover\sStatus.*:\sFAILURE"
    SWITCH_OVER_NO_HEALTHY_UPSTREAM = (
        r"Error\sMessage.*:.*Secondary\ssite\sswitchover\sprocess\shas\sfailed"
    )
    BACKUP_ID = r"Backup\sId\s+:\s(.*?)\n"
    SWITCHOVER_NO_FREE_MEMORY = (
        r"\{\"statusCode\":500,\"message\":\"Error handling persisted file\"\}"
    )

    # Geo Recovery
    RECOVERY_STATUS = r"clusterStatus':\s*'([^']+)"
    RECOVERABLE_STATUS_AFTER_UPDATE = (
        r"Cluster\s{cluster}\sstatus\safter\supdate-recovery-state\sis\sRECOVERABLE"
    )


class GrTimeouts:
    """
    Geo Redundancy timeouts
    """

    IMAGE_SYNC = 900  # 15 min
    AVAILABILITY = 300  # 5 min
    RECOVERY_POD_CHECK = 900  # 15 min
    RECOVERY_POD_CHECK_CUSTOM = 120  # 2 min
    GR_CONTROLLER_POD_UP_STATE = 1800  # 30 min
    SWITCHOVER_TIMEOUT = 5400  # 1.5 hours


class SwitchoverPods:
    """
    Pods that must be up and running on active site and not available on passive after a successful switchover
    """

    HEALTH_CHECK_LIST_CVNFM = [
        COMMON_WFS,
        EVNFM_NBI,
        VNFM_ORCHESTRATOR_SERVICE,
        EO_AM_ONBOARDING,
        ERIC_EO_EVNFM_CRYPTO,
        ERIC_EO_LM_CONSUMER,
        ERIC_EO_USERMGMT,
        EVNFM_TOSCAO,
    ]
    COMPLETE_HEALTH_CHECK_LIST = HEALTH_CHECK_LIST_CVNFM + [VNFLCM_SERVICE]


class GeoRecoveryStatuses:
    """
    Geo recovery status command possible site statuses
    """

    RECOVERABLE = "RECOVERABLE"
    NOT_RECOVERABLE = "NOT_RECOVERABLE"
    RECOVERY_IN_PROGRESS = "RECOVERY_IN_PROGRESS"


class GrStatusSiteInfoStates:
    """
    Stores gr status site info keys
    """

    OK = "OK"
    FAILED = "FAILED"


class GrBurOrchestratorDeploymentEnvVars:
    """
    Stores Environment Vars that are used in Bur Orchestrator deployment
    """

    POD_UP_STATE_TIMEOUT = "PODS_UP_STATE_SHORT_TIMEOUT_SECONDS"
    LOG_LEVEL = "LOG_LEVEL"
    GR_PRIMARY_CYCLE_INTERVAL = "GR_PRIMARY_CYCLE_INTERVAL_SECONDS"
    IMAGE_SYNC_INTERVAL_PRIMARY = "IMAGE_SYNC_CHECK_CYCLE_INTERVAL_SECONDS_PRIMARY"


class SiteRoles:
    """Stores roles for GR Sites"""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class GrActiveApps:
    """Stores possible value for GR Active Application property"""

    EVNFM = "evnfm"
    VMVNFM = "vmvnfm"
