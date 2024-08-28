"""Storing constants related to iperf tool"""

from pathlib import Path


class IperfServerPaths:
    """Paths related to iperf"""

    SERVICE_CONFIG = Path("resources/iperf3/iperf-service.yaml")
    SERVER_POD_CONFIG = Path("resources/iperf3/iperf-server-pod.yaml")


class IperfCmds:
    """Iperf tool cli commands"""

    CLIENT = "iperf3 -c {} -f m"
