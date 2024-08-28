"""Module with PodsHealthChecker class"""

from core_libs.common.custom_exceptions import PodsStatusCheckFailedError

from apps.codeploy.codeploy_app import CodeployApp
from libs.utils.logging.logger import logger


class PodsHealthChecker:
    """Class that contains methods for check of pods health"""

    def __init__(
        self,
        *,
        active_site_codeploy: CodeployApp,
        passive_site_codeploy: CodeployApp | None = None
    ):
        self.active_site_codeploy = active_site_codeploy
        self.passive_site_codeploy = passive_site_codeploy

    def healthcheck(
        self,
    ) -> None:
        """
        Method makes common heath check of pods for provided sites
        """
        self.check_pods_health()
        self.check_failed_pods()
        logger.info(
            "Completed. Pods healthcheck and failed pods check passed successfully."
        )

    def check_pods_health(self) -> None:
        """
        Methods that checks pods health
        Raises:
            PodsStatusCheckFailedError: raises if pods are not healthy
        """
        active_site_unhealthy = self.active_site_codeploy.pods_health_check(
            should_pods_exists=True
        )
        passive_site_unhealthy = (
            self.passive_site_codeploy
            and self.passive_site_codeploy.pods_health_check(should_pods_exists=False)
        )
        if active_site_unhealthy or passive_site_unhealthy:
            raise PodsStatusCheckFailedError(
                active_site_unhealthy + passive_site_unhealthy
            )

    def check_failed_pods(self) -> None:
        """
        Methods that checks failed pods
        Raises:
            PodsStatusCheckFailedError: raises if pods are not healthy
        """
        active_site_unhealthy = self.active_site_codeploy.failed_pods_check()
        passive_site_unhealthy = (
            self.passive_site_codeploy
            and self.passive_site_codeploy.failed_pods_check()
        )
        if active_site_unhealthy or passive_site_unhealthy:
            raise PodsStatusCheckFailedError(
                active_site_unhealthy + passive_site_unhealthy
            )
