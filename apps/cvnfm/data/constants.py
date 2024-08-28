"""Module with CVNFM related data"""


class PackageStates:
    """Class for CVNFM package states"""

    ENABLED = "ENABLED"
    NOT_IN_USE = "NOT_IN_USE"


class PackageFields:
    """Class for CVNFM package fields"""

    USAGE_STATE = "usageState"
    OPERATIONAL_STATE = "operationalState"


class InstantiationStates:
    """Class for CVNFM Instance instantiation state"""

    INSTANTIATED = "INSTANTIATED"
    NOT_INSTANTIATED = "NOT_INSTANTIATED"


class OperationFields:
    """Class for CVNFM Instance Operations fields"""

    OPERATION = "operation"
    OPERATION_STATE = "operationState"


class CommonFields:
    """Class for CommonFields"""

    ADDITIONAL_PARAMS = "additionalParams"
    APPLICATION_TIME_OUT = "applicationTimeOut"
    NAMESPACE = "namespace"


class PackageTestValues:
    """Class to describe information of values used during testing"""

    ASPECT = "Aspect5"


class CvnfmDefaults:
    """
    Class to keep default values of CVNFM app
    """

    DEFAULT_CISM_CLUSTER_NAME = "default_cluster.config"
    CNF = "cnf"
