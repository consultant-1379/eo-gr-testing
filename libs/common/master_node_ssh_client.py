"""
Module that includes functionality for accessing EO master node and its workers through the SSH
"""

from shlex import quote

import paramiko
from core_libs.common.ssh import SSHClient, SSHResult

from libs.utils.logging.logger import logger, log_exception


class SSHMasterNode(SSHClient):
    """Class that allows establishing SSH sessions to the master and worker nodes"""

    def __init__(
        self,
        hostname: str,
        *,
        username: str | None = None,
        password: str | None = None,
        key_filename: str | None = None,
        worker_ip: str | None = None,
        worker_username: str | None = None,
        worker_password: str | None = None,
    ) -> None:
        super().__init__(
            hostname, username=username, password=password, key_filename=key_filename
        )
        self.hostname = hostname
        self.username = username
        self.key_filename = key_filename
        self.worker_ip = worker_ip
        self.ssh_port = 22
        self.worker_username = worker_username
        self.worker_password = worker_password
        self.worker_client = None
        self.worker_host = None
        self._tcp_forwarding_enabled = False

    def connect(
        self, timeout: int = 60 * 2, on_worker: bool = False, **kwargs
    ) -> SSHClient:
        """
        Connect and authenticate to the master node through SSH
        Args:
            on_worker: if necessary, establish a connection on the worker node, passing by the master (jump host)
            timeout: Connection timeout
            **kwargs: Other Paramiko's Client.connect() parameters
        Raises:
            TimeoutError if no SSH connection is established before timeout expiration
        Returns:
            SSHMasterNode instance
        """
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.host = (
                f"{self.username}@{self.hostname}" if self.username else self.hostname
            )
            logger.info(f"Connecting via SSH to {self.host}")

            self.client.connect(
                self.hostname,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=timeout,
                **kwargs,
            )
            if on_worker:
                if not (self.worker_ip and self.worker_username):
                    raise ValueError(
                        "To establish connection on worker Node worker's IP and worker's username should be provided!"
                    )
                if self._tcp_forwarding_enabled is False:
                    # allways allow TCP forwarding once for connecting to worker's Node
                    self.allow_tcp_forwarding()
                    self._tcp_forwarding_enabled = True

                self.worker_host = f"{self.worker_username}@{self.worker_ip}"
                logger.info(
                    f"Establishing connection to master's worker {self.worker_host}..."
                )
                self.worker_client = self.establish_jump_connection(
                    user_name=self.worker_username,
                    host=self.worker_ip,
                    password=self.worker_password,
                )

        except paramiko.ssh_exception.AuthenticationException:
            # Allows connection with an empty password
            if self.password is None:
                self.client.get_transport().auth_none(self.username)
            else:
                raise
        except paramiko.ssh_exception.SSHException as exc:
            if "SSH negotiation failed" in exc.args[0]:
                raise TimeoutError(
                    log_exception(
                        f"Could not connect to {self.host} during {timeout} seconds"
                    )
                ) from exc
            raise

        return self

    def exec_cmd(
        self,
        cmd: str | list,
        verify_exit_code: bool = True,
        stdout_only: bool = True,
        *,
        on_worker: bool = False,
        **kwargs,
    ) -> str | SSHResult:
        """
        Run a command either on the master or on the worker node
        Args:
            cmd: Command to run in terminal
            verify_exit_code: Determines, if result must be checked for an exit-code
            stdout_only: method return only stdout if true else SSHResult instance
            on_worker: Run a command on the worker node, passing by the director (jump host)
            kwargs: Other parameters of Paramiko's exec_command() method
        Raises:
            ConnectionError: if command was sent with a closed session
            RuntimeError: if the command execution completed with non-zero exit code
            AttributeError: if the command has unexpected attribute
            TimeoutError: if timeout for read stdout/stderr output ran out
        Returns:
            Command execution STDOUT or SSHResult instance
        """
        if not self.is_active():
            self.connect(on_worker=on_worker)

        if isinstance(cmd, list):
            cmd = " ".join([quote(str(i)) for i in cmd])

        host_pattern = "-> [{}] "
        log_message_pattern = "SSH {host}CMD: {cmd}"
        host = host_pattern.format(self.host)

        try:
            if on_worker:
                self.connect(on_worker=on_worker)
                host += host_pattern.format(self.worker_host)
                # establishing jump connection
                with self.worker_client as worker_client:
                    result = self.ssh_result(worker_client.exec_command(cmd, **kwargs))
            else:
                result = self.ssh_result(self.client.exec_command(cmd, **kwargs))

            log_message = log_message_pattern.format(host=host, cmd=cmd)

            if result.stdout:
                log_message += f"\nSTDOUT: {result.stdout}"
            if result.stderr:
                log_message += f"\nSTDERR: {result.stderr}"
            logger.info(log_message)

            if result.exit_code != 0:
                err_txt = (
                    f"Command {cmd} exited with a non-zero code ",
                    f"{result.exit_code}, STDERR: {result.stderr}",
                )

                if verify_exit_code:
                    raise RuntimeError(log_exception(err_txt))
            return result.stdout if stdout_only else result

        except AttributeError as exc:
            if "open_session" in exc.args[0]:
                raise ConnectionError(
                    log_exception("SSH connection was not established")
                ) from exc
            raise
        except TimeoutError:
            log_message = log_message_pattern.format(host=host, cmd=cmd)
            logger.info(log_message)
            raise

    @staticmethod
    def ssh_result(raw_ssh_result: tuple) -> SSHResult:
        """
        Return SSHResult dataclass instance
        Args:
            raw_ssh_result: the stdin, stdout, and stderr of the executing command, as a 3-tuple
        Returns:
            SSHResult dataclass
        """
        _, stdout, stderr = raw_ssh_result
        return SSHResult(
            stdout=stdout.read().decode().rstrip("\n"),
            stderr=stderr.read().decode(),
            exit_code=stdout.channel.recv_exit_status(),
        )
