"""Module with ClusterSecrets data"""
from json import dumps

from core_libs.common.misc_utils import encode_to_base64_string


class ClusterSecrets:
    """
    ClusterSecrets class
    """

    HELM_CHART_REGISTRY = {
        "name": "eric-lcm-helm-chart-registry",
        "data": {
            "helm_user": "BASIC_AUTH_USER",
            "helm_pwd": "BASIC_AUTH_PASS",
            "helm_url": "url",
        },
    }
    DOCKER_REGISTRY = {
        "name": "container-credentials",
        "data": {
            "docker_user": "userid",
            "docker_pwd": "userpasswd",
            "docker_url": "url",
        },
    }


def get_snmp_alarm_provider_secrets_data(ro_snmp_ip: str) -> dict:
    """Get data to create alarm secret
    Args:
        ro_snmp_ip: SNMP IP address
    Returns:
        secret data
    """
    # some data is intentionally hard-coded
    config_content = {
        "agentEngineId": "12abc1b804c162d0",
        "trapTargets": [{"address": ro_snmp_ip, "community": "public"}],
    }
    return {"config.json": encode_to_base64_string(dumps(config_content))}
