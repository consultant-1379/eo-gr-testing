"""
This module contains a class of services names for VM VNFM
"""


class VmvnfmServiceNames:
    """
    VM VNFM service names
    """

    NFVO = "nfvo"
    EM = "em"
    VIM = "vim"
    WORKFLOW = "workflow"
    VNF = "vnf"


class VmvnfmServiceTexts:
    """
    VM VNFM service success, info, error texts
    """

    NOT_FOUND = "No {} found to list"
    NO_DATA = "No data to display"
    SUCCESS = "{} addition successful"
    DELETE_SUCCESS = "{} deleted successfully"

    @staticmethod
    def format_text(service_name, msg):
        """

        :param service_name: A service name
        :type service_name: str
        :param msg: A message
        :type msg: str
        :return: a formatted message
        :rtype: str
        """
        return msg.format(service_name.upper())


class VmvnfmServiceLabel:
    """
    VM VNFM service labels
    """

    PRE_REGISTERED = "PRE_REGISTERED"
