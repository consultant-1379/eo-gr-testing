"""Stores ThreadRunner class which is the wrapper over Thread class from threading lib"""

from threading import Thread
from time import sleep
from typing import Any

from core_libs.common.logger import logger

from libs.common.custom_exceptions import (
    ConditionIsNotMetWhileThreadAliveError,
    ThreadTimeoutExpiredError,
)


class ThreadRunner(Thread):
    """Class is the wrapper over Thread class"""

    def __init__(
        self,
        target: callable,
        *,
        name=None,
        args: tuple | list | None = None,
        kwargs: dict | None = None,
        daemon: bool | None = None,
    ):
        """
        Note: if daemon is True this thread is automatically terminated when the program (main thread) exits,
            regardless of whether it have completed its work.
        """
        name = name if not name else f"{name}: {target.__qualname__}"
        super().__init__(
            target=target, name=name, args=args or (), kwargs=kwargs, daemon=daemon
        )
        self._return = None

    def run(self) -> None:
        """Overridden parent class method with return value functionality"""
        logger.info(f"New thread: [ {self.name} ] is running")
        self._return = self._target(*self._args, **self._kwargs)

    def join_with_result(self, timeout: int | None = None) -> Any:
        """Join thread to main thread and wait until the thread terminates and return thread's result
        Raises:
            ThreadTimeoutExpiredError: when timeout for thread execution ran out
        Returns:
            thread's result
        """
        super().join(timeout=timeout)

        if timeout and self.is_alive():
            raise ThreadTimeoutExpiredError(
                f"Thread: [ {self.name} ] is still alive after expiring {timeout=}!"
            )

        logger.info(f"Thread: [ {self.name} ] finished")
        return self._return

    def wait_for_condition_while_thread_is_alive(
        self, condition: callable, interval: int = 15, raise_exc: bool = True
    ) -> bool:
        """Waits for condition to become True or False while thread is alive
        Args:
            condition: callable object that returns boolean value
            interval: interval between condition verification attempts
            raise_exc: flag that define if ConditionIsNotMetWhileThreadAliveError need to be raised or not
        Raises:
            ConditionIsNotMetWhileThreadAliveError: when condition is not met and raise_exc=True
        Returns:
            True if condition is met, False otherwise if raise_exc=False
        """
        condition_name = condition.__qualname__
        logger.info(
            f"Start waiting for {condition_name} while thread {self.name} is alive"
        )
        while self.is_alive():
            if condition():
                logger.info(f"Condition {condition_name} is met")
                return True
            sleep(interval)
        exc_msg = f"Condition {condition_name} is not met. Thread {self.name} has been finished."
        if raise_exc:
            raise ConditionIsNotMetWhileThreadAliveError(exc_msg)
        logger.info(exc_msg)
        return False
