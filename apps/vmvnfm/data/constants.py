"""
Module with VMVNFM constants
"""
from dataclasses import dataclass, field
from pathlib import Path

from core_libs.common.misc_utils import generate_asset_test_name
from core_libs.eo.eocm.eocm_constants import PackagesFormats

from libs.common.constants import CommonNames


@dataclass
class VnfDeploymentData:
    """
    VNF Deployment Data
    """

    vnfm_id: str
    tenant_name: str
    vim_zone_name: str
    vdc_id: str
    flavor: str
    image_name: str = field(init=False)
    cidr: str
    vn_vim_zone_id: str
    external_ip_for_mgmnt_node_oam: str
    external_subnet_gateway: str
    vapp_name: str = generate_asset_test_name("vapp", root_name=CommonNames.EOGR)
    vapp_id: str | None = None
    srt_id: str | None = None


@dataclass
class VnfUnclassifiedData:
    """
    Unclassified package data for uploading/deploying package
    """

    vnf_manager: str
    tenant_name: str
    vim_zone_name: str
    version: str
    software_version: str
    services_flavor: str
    flavor_id: str
    vim_image_name: str
    cidr: str
    vn_vim_zone_id: str
    external_ip_for_mgmnt_node_oam: str
    external_subnet_gateway: str
    package_format: str = PackagesFormats.EXTERNAL_FORMAT
    vapp_name: str = generate_asset_test_name(
        "vapp_unclassified", root_name=CommonNames.EOGR
    )
    vapp_id: str | None = None
    vdc_id: str | None = None
    package_id: str | None = None


class VmvnfmPaths:
    """Class for store VMVNFM Paths"""

    PACKAGES_REPO = "/vnflcm-ext/current/vnf_package_repo/"
    ENVIRONMENT_FILES = (
        f"{PACKAGES_REPO}{{descriptor_id}}/HOT/Resources/EnvironmentFiles/"
    )
    SERVER_LOG = Path("/ericsson/3pp/jboss/standalone/log/server.log")
    WFMGR_CLI_LOG = Path("/var/log/wfmgr-cli-log/logfile.log")
    APACHE_LOGS = Path("/var/log/apache2/")
