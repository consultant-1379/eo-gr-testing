"""module for VmvmfmMArtefactModel class"""

from dataclasses import dataclass


@dataclass
class VmvnfmArtefactModel:
    """VMVNFM Artefact Model"""

    url: str
    srt_ram: int | None
    srt_cpu: int | None
    srt_disc_size: int | None
    descriptor_id: str | None
    path: str | None = None
    package_id: str | None = None
