"""
File with custom exceptions
"""


class DockerRegistryAvailabilityError(Exception):
    """
    Exception raises when docker registry not available
    """


class EnvironmentVariableNotProvidedError(Exception):
    """
    Exception raises when Environment Variable not provided by user
    """


class SwitchoverInstallationError(Exception):
    """
    Exception raises when switchover installation error
    """


class UnexpectedResponseContentError(Exception):
    """
    Exception raises when response contains unexpected content
    """


class UnexpectedNumberOfCnfInstances(Exception):
    """
    Exception raises when response contains unexpected number of CNF instances
    """


class GrBackupIdNotFoundError(Exception):
    """
    Exception raises when back up id can't be found in GR availability or GR status
    """


class GrStatusOutputMissmatchError(Exception):
    """
    Exception raises when GR Status Output value has not expected value
    """


class GrStatusOutputError(Exception):
    """
    Exception raises when GR Status contains errors
    """


class GrRecoveryStatusNotFound(Exception):
    """
    Exception raises when Geo Recovery Status output hasn't status value
    """


class DeploymentManagerVersionError(Exception):
    """Exception raises when error with obtaining DM version occurs"""


class DnsSettingsError(Exception):
    """Exception raises when any error with DNS occurs"""


class DnsServerIsNotDeployed(Exception):
    """Raises if DNS server was not deployed"""


class WrongDnsIpError(Exception):
    """Raises when DNS IP is wrong"""


class ConditionIsNotMetWhileThreadAliveError(Exception):
    """Exception raises when condition is not while thread is alive"""


class ThreadTimeoutExpiredError(Exception):
    """Exception raises when timeout for thread execution ran out"""


class MasterNodeNotFoundError(Exception):
    """Exception raises when master node is not found"""


class MissingKeyInConfigMapError(Exception):
    """Exception raises when expected key is missing from ConfigMap"""
