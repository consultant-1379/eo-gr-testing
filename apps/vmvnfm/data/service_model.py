"""
This module contains a class of service model for VM VNFM
"""

from dataclasses import dataclass, field


@dataclass
class VmvnfmServiceModel:
    """
    VM VNFM service model
    """

    name: str
    template: str
    add_success_text: str
    delete_success_text: str
    not_found_text: str
    alternative_not_found_text: str
    config_path: str = ""
    labels: list = field(default_factory=list)
