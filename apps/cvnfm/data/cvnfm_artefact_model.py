"""
This module contains a class of artifact model for CVNFM
"""
# pylint: disable=C0103

from dataclasses import dataclass, field


@dataclass
class CvnfmArtifactModel:
    """
    CVNFM artifact model
    """

    url: str
    onboarding_timeout: str
    lcm_timeout: str
    actions: list = field(default_factory=list)
    path: str | None = None
    descriptor_id: str | None = None
    additional_config: str | None = None
    additional_config_modify: str | None = None
    additional_config_scale: str | None = None
    package_id: str | None = None
