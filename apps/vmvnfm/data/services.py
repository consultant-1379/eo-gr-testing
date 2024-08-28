"""
This module contains data of VM VNFM services
"""
from apps.vmvnfm.data.service_data import (
    VmvnfmServiceNames as Name,
    VmvnfmServiceTexts as Text,
)
from apps.vmvnfm.data.service_model import VmvnfmServiceModel

NFVO_SERVICE = VmvnfmServiceModel(
    name=Name.NFVO,
    template="template_nfvoconfig.json",
    add_success_text=Text.format_text(Name.NFVO, Text.SUCCESS),
    delete_success_text=Text.format_text(Name.NFVO, Text.DELETE_SUCCESS),
    not_found_text=Text.format_text(Name.NFVO, Text.NOT_FOUND),
    alternative_not_found_text=Text.NO_DATA,
)
EM_SERVICE = VmvnfmServiceModel(
    name=Name.EM,
    template="template_em_config.json",
    add_success_text=Text.format_text(Name.EM, Text.SUCCESS),
    delete_success_text=Text.format_text(Name.EM, Text.DELETE_SUCCESS),
    not_found_text=Text.format_text(Name.EM, Text.NOT_FOUND),
    alternative_not_found_text=Text.NO_DATA,
)
VIM_SERVICE = VmvnfmServiceModel(
    name=Name.VIM,
    template="template_vim.json",
    add_success_text=Text.format_text(Name.VIM, Text.SUCCESS),
    delete_success_text=Text.format_text(Name.VIM, Text.DELETE_SUCCESS),
    not_found_text=Text.format_text(Name.VIM, Text.NOT_FOUND),
    alternative_not_found_text=Text.NO_DATA,
)
WORKFLOW_SERVICE = VmvnfmServiceModel(
    name=Name.WORKFLOW,
    template="",
    add_success_text="package installation successful",
    delete_success_text="Package uninstalled successfully",
    not_found_text="",
    alternative_not_found_text="",
)

ECM_SERVICES = [NFVO_SERVICE, EM_SERVICE]
