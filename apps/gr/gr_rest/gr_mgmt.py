"""Module to store GR API REST management class"""

from requests import Response

from core_libs.common.base_rest import BaseREST

from apps.gr.gr_rest.rest_constants import GrRestPaths


class GrApiMgmt(BaseREST):
    """Class to interact with GR REST API related operations"""

    def get_metadata(self) -> Response:
        """Get GR cluster metadata
        Returns:
            http response
        """
        return self.get(f"{self.url}{GrRestPaths.METADATA}")
