"""Module to store data related to GR REST API"""


class GrRestPaths:
    """Store GR REST API related paths"""

    _API_V1 = "/api/v1"

    METADATA = f"{_API_V1}/clusters/metadata"


class GrRestKeys:
    """Constant keys related to GR API"""

    ROLE = "role"
    ACTIVE_APPS = "activeApplications"
