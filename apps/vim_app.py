""" Module with VimApp class"""
from core_libs.common.constants import VimConfigKeys
from core_libs.common.misc_utils import generate_asset_test_name
from core_libs.eo.eocm.eocm_constants import EocmDefaults

from libs.common.constants import CommonNames
from libs.utils.logging.logger import logger


class VimApp:
    """
    VimApp class contains all methods related to VIM and then used as test steps
    """

    def __init__(self, config):
        self.config = config
        self.vim_name = generate_asset_test_name(
            EocmDefaults.VIM, root_name=CommonNames.EOGR
        )

    @property
    def host(self):
        """A VIM host property"""
        return self.config.read_section(VimConfigKeys.VIM_HOST)

    @property
    def url(self):
        """A URL host property"""
        return self.config.read_section(VimConfigKeys.URL)

    @property
    def os_auth_url(self):
        """A OS_AUTH_URL property"""
        return self.config.read_section(VimConfigKeys.OS_AUTH_URL)

    @property
    def os_default_project_name(self):
        """A OS_DEFAULT_PROJECT_NAME property"""
        return self.config.read_section(VimConfigKeys.OS_DEFAULT_PROJECT_NAME)

    @property
    def os_default_project_admin_password(self):
        """A OS_DEFAULT_PROJECT_ADMIN_PASSWORD  property"""
        return self.config.read_section(VimConfigKeys.OS_DEFAULT_PROJECT_ADMIN_PASSWORD)

    @property
    def os_default_project_admin(self):
        """A OS_DEFAULT_PROJECT_ADMIN property"""
        return self.config.read_section(VimConfigKeys.OS_DEFAULT_PROJECT_ADMIN)

    @property
    def os_endpoints(self):
        """A OS_ENDPOINTS property"""
        return self.config.read_section(VimConfigKeys.OS_ENDPOINTS)

    @property
    def project_name(self):
        """A PROJECT_NAME property"""
        return self.config.read_section(VimConfigKeys.PROJECT_NAME)

    @property
    def vim_type(self):
        """
        A VIM_TYPE property
        """
        return self.config.read_section(VimConfigKeys.VIM_TYPE)

    @property
    def project_domain_id(self):
        """A OS_PROJECT_DOMAIN_ID property"""
        return self.config.read_section(VimConfigKeys.OS_PROJECT_DOMAIN_ID)

    @property
    def domain_name(self):
        """A domain_name property"""
        return self.config.read_section(VimConfigKeys.OS_USER_DOMAIN_ID)

    @property
    def admin_user_name(self):
        """A admin_user_name property"""
        return self.config.read_section(VimConfigKeys.OS_PROJECT_ADMIN_USERNAME)

    @property
    def admin_password(self):
        """A admin_password property"""
        return self.config.read_section(VimConfigKeys.OS_PROJECT_ADMIN_PASSWORD)

    @property
    def user_name(self):
        """A user_name property"""
        return self.config.read_section(VimConfigKeys.OS_PROJECT_USER_USERNAME)

    @property
    def user_password(self):
        """A user_password property"""
        return self.config.read_section(VimConfigKeys.OS_PROJECT_USER_PASSWORD)

    @property
    def vim_obj_id(self):
        """A vim_object_id property"""
        return self.config.read_section(VimConfigKeys.VIM_OBJECT_ID)

    @property
    def admin_vim_obj_id(self):
        """A admin_vim_obj_id property"""
        return self.config.read_section(VimConfigKeys.OS_ADMIN_VIM_OBJECT_ID)

    @property
    def user_vim_object_id(self):
        """A user_vim_object_id property"""
        return self.config.read_section(VimConfigKeys.OS_USER_VIM_OBJECT_ID)

    def prepare_data_for_vmvnfm_integration(self, default_vim=True):
        """
        Prepares data for registration a VIM instance in VMVNFM
        :param default_vim: defines if VIM should be default
        :type default_vim: boolean
        :return: VIM registration data for VMVNFM
        :rtype: dict
        """
        logger.info("Preparing registration data for the integration with VMVNFM")
        project = {
            "name": self.os_default_project_name,
            "id": self.vim_obj_id,
            "username": self.os_default_project_admin,
            "password": self.os_default_project_admin_password,
            "defaultProject": "True",
        }
        domain = {
            "userDomain": self.domain_name,
            "name": self.domain_name,
            "id": self.config.read_section(VimConfigKeys.OS_PROJECT_DOMAIN_ID),
            "defaultDomain": "True",
            "project": [project],
        }
        vim = {
            "name": self.vim_name,
            "type": self.vim_type,
            "defaultVim": str(default_vim),
            "hostIpAddress": self.config.read_section(VimConfigKeys.VIM_IP),
            "hostName": self.host,
            "authUrl": self.config.read_section(VimConfigKeys.OS_AUTH_URL),
            "domain": [domain],
        }
        return vim
