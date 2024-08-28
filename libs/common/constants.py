"""
This defines the constant variable key used in configurations.
"""

import os
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent.parent
DEFAULT_DOWNLOAD_LOCATION = str(ROOT_PATH / "downloads") + os.sep
UTF_8 = "utf-8"
EO_GR_LOGGER_NAME = "eo_gr"
LOCAL_LOG_DIR = ROOT_PATH / "downloaded_logs"
DEFAULT_NAME = "default-name"
GR_TEST_PREFIX = "gr-test"
ENV_PROPERTIES_FILE = ROOT_PATH / "env.properties"


class ConfigFilePaths:
    """
    Class to store constant paths/path formats for config files
    """

    ENV_CONF = "env_{}.yaml"
    VIM_CONF = "vim_{}.yaml"
    CONFIG_FOLDER = ROOT_PATH / "config"
    ENVS_FOLDER = CONFIG_FOLDER / "envs"
    VIMS_FOLDER = CONFIG_FOLDER / "vims"
    COMMON_CONFIG = CONFIG_FOLDER / "common_config.yaml"
    ARTEFACTS = CONFIG_FOLDER / "artefacts.yaml"
    SFTP_AND_DNS_FOLDER = CONFIG_FOLDER / "sftp_and_dns"


class LoggingConfigPath:
    """
    Class to store constant paths/path formats for logging config files
    """

    LOGGING_CONFIG = ROOT_PATH / "libs/utils/logging/logging_config.yaml"


class GrEnvVariables:
    """
    Class to store Env Variables to be used in framework
    """

    ACTIVE_SITE = "ACTIVE_SITE"
    RESOURCES_CLEAN_UP = "RESOURCES_CLEAN_UP"
    PASSIVE_SITE = "PASSIVE_SITE"
    DEPLOYMENT_MANAGER_DOCKER_IMAGE = "DEPLOYMENT_MANAGER_DOCKER_IMAGE"
    DEPLOYMENT_MANAGER_VERSION = "DEPLOYMENT_MANAGER_VERSION"
    HOST_LOCAL_PWD = "HOST_LOCAL_PWD"
    GR_STAGE_SHARED_NAME = "GR_STAGE_SHARED_NAME"
    EO_VERSIONS_COLLECTION = "EO_VERSIONS_COLLECTION"
    RV_SETUP = "RV_SETUP"
    DM_LOG_LEVEL = "DM_LOG_LEVEL"
    DNS_SERVER_IP = "DNS_SERVER_IP"
    DNS_FLAG = "DNS_FLAG"
    DOCKER_CONFIG = "DOCKER_CONFIG"
    GLOBAL_REGISTRY = "GLOBAL_REGISTRY"
    ENABLE_VMVNFM_DEBUG_LOG_LEVEL = "ENABLE_VMVNFM_DEBUG_LOG_LEVEL"


class UtilScriptsEnvVarConst:
    """Stores environment variables constants related to util scripts only"""

    LOG_PREFIX = "LOG_PREFIX"


class GrConfigKeys:
    """
    Class to store GR config Keys
    """

    GR_ORIGINAL_PRIMARY = "GR_ORIGINAL_PRIMARY"
    GR_HOST = "GR_HOST"
    GR_USER_NAME = "GR_USER_NAME"
    GR_USER_PASSWORD = "GR_USER_PASSWORD"
    DNS_CLIENT_HOST = "DNS_CLIENT_HOST"
    DNS_CLIENT_USER = "DNS_CLIENT_USER"
    DNS_CLIENT_PASSWORD = "DNS_CLIENT_PASSWORD"
    DNS_SERVER_NAMESPACE = "DNS_SERVER_NAMESPACE"
    DNS_SERVER_CLUSTER_NAME = "DNS_SERVER_CLUSTER_NAME"
    DNS_SERVER_KUBE_CONFIG = "DNS_SERVER_KUBE_CONFIG"
    DNS_SERVER_EX_IP_ADDRESS = "DNS_SERVER_EX_IP_ADDRESS"
    SFTP_NAMESPACE = "SFTP_NAMESPACE"
    SFTP_CLUSTER_NAME = "SFTP_CLUSTER_NAME"
    SFTP_KUBE_CONFIG = "SFTP_KUBE_CONFIG"
    SFTP_EXT_IP_ADDRESS = "SFTP_EXT_IP_ADDRESS"
    SFTP_USER_NAME = "SFTP_USER_NAME"
    SFTP_PASSWORD = "SFTP_PASSWORD"


class EvnfmConfigKeys:
    """
    Class to store keys to read EVNFM data from env config files
    """

    EVNFM_HOST = "EVNFM_HOST"

    EVNFM_DEFAULT_USER_NAME = "EVNFM_DEFAULT_USER_NAME"
    EVNFM_DEFAULT_USER_PASSWORD = "EVNFM_DEFAULT_USER_PASSWORD"
    EVNFM_DEFAULT_TENANT = "EVNFM_DEFAULT_TENANT"
    PV_STORAGE_CLASS = "PV_STORAGE_CLASS"

    EVNFM_USER_NAME = "EVNFM_USER_NAME"
    EVNFM_USER_PASSWORD = "EVNFM_USER_PASSWORD"


class EoVersionsFiles:
    """
    Stores constant paths formats for EO versions files
    """

    VERSIONS_TEMPLATE = ROOT_PATH / "tests/reporter_templates/eo_versions.html"
    VERSIONS_REPORT = ROOT_PATH / "versions_report.html"


class CommonNames:
    """
    Stores common application names
    """

    EOGR = "eogr"


class EoApps:
    """
    Stores EO applications
    """

    _ERIC_EO = "eric-eo"

    CVNFM = f"{_ERIC_EO}-evnfm"
    VMVNFM = f"{_ERIC_EO}-evnfm-vm"


class EoPackages:
    """
    Stores EO packages
    """

    HELM_FILE = "helmfile"
    DM = "deployment-manager"


class InstalledAppConfigMapKeys:
    """
    Stores keys for "eric-installed-applications" configmap
    """

    RELEASE = "release"
    INSTALLED = "Installed"
    CSAR = "csar"
    NAME = "name"
    VERSION = "version"


class DockerRegistryKeys:
    """
    Stores Docker Registry Keys
    """

    REPOSITORIES = "repositories"


class DockerRegistryV2ApiPaths:
    """
    Stores url paths for Docker Registry V2 API
    """

    REPOSITORIES = "v2/_catalog"
    TAGS = "v2/{repository}/tags/list"


class YamlTags:
    """
    Stores tags for YAML files
    """

    FROM_KEY = "!from_key"


class DockerFlags:
    """Stores Docker related flags"""

    DNS = "--dns {}"
