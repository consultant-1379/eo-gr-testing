"""
Module for store E-VNFM related data
"""


DEFAULT_EVNFM_APP_TIMEOUT = 900


class OperationFields:
    """Class for E-VNFM Instance Operations fields"""

    OPERATION = "operation"
    OPERATION_STATE = "operationState"


class InstanceFields:
    """Class for CVNFM Instance fields"""

    INSTANTIATION_STATE = "instantiationState"
    VNF_PKG_ID = "vnfPkgId"
    VNF_INSTANCE_DESCRIPTION = "vnfInstanceDescription"
    VNF_INSTANCE_NAME = "vnfInstanceName"
    METADATA = "metadata"
    EXTENSIONS = "extensions"
