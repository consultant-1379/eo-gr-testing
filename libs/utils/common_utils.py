"""Module with common utils"""
import asyncio
import re
import socket
import subprocess
from operator import gt, ge, lt, le, eq, ne
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess

import yaml
from packaging import version
from jinja2 import Environment, FileSystemLoader

from libs.common.constants import ROOT_PATH, ConfigFilePaths, UTF_8
from libs.utils.logging.logger import logger, log_exception


def search_with_pattern(
    pattern: str, text: str, *, dotall: bool = False, group: int = 1
) -> str | None:
    """
    Search in text by regex pattern
    Args:
        pattern: regex pattern
        text: text in which to search
        dotall: include new line character
        group: re group to return
    Returns:
        Search result
    """
    logger.debug(f"Searching for '{pattern=}'")
    result = re.search(pattern, text, re.DOTALL if dotall else 0)
    return result and result.group(group)


def is_pattern_match_text(
    pattern: str, text: str, *, dotall: bool = False, group: int = 1
) -> bool:
    """
    Search in text by regex pattern and return boolean value of result
    Args:
        pattern: regex pattern
        text: text in which to search
        dotall: include new line character
        group: re group to return
    Returns:
        True if text match else Fasle
    """
    return bool(
        search_with_pattern(pattern=pattern, text=text, dotall=dotall, group=group)
    )


def get_datetime_from_str(
    string: str, pattern: str = "%Y-%m-%d %I:%M:%S %p"
) -> datetime:
    """
    Parse string to datetime object by pattern
    Args:
        string: string to parse
        pattern: format pattern
    Returns:
        Datetime object
    """
    return datetime.strptime(string, pattern)


def run_shell_cmd(
    cmd: str | list,
    timeout: int | None = 60,
    log_stdout: bool = True,
    check_return_code: bool = True,
    **kwargs,
) -> CompletedProcess:
    """
    Wrapper around subprocess.run. Returns CompletedProcess instance and
    additionally will log command's arguments, stdin, stdout, return code.

    All arguments follow subprocess.run interface.
    Setting log_stdout to False disables command output logging
    Args:
        cmd: Target shell command
        timeout: Timeout for the command execution. When expires it raises the TimeoutError exception
                 after the child process has terminated
        log_stdout: Flag to enable or disable command output logging
        check_return_code: Flag to enable or disable return code checking.
                            If enable and return code =! 0 will rise an exception
        **kwargs: other keyword parameters
    Raise:
        TimeoutError: when command execution timeout expired
        RuntimeError: when command exits with non-zero code
    Returns:
        CompletedProcess instance
    """
    logger.info(f"Executing {cmd=}")

    try:
        proc = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
            shell=True,
            check=False,
            **kwargs,
        )
    except subprocess.TimeoutExpired as e:
        raise TimeoutError from e

    log_message = (
        "Command executing {status}:\n"
        "CMD: {cmd}\n"
        "STDOUT:{stdout}\n"
        "STDERR:{stderr}\n"
        "Returncode: {returncode}"
    )

    if log_stdout:
        stdout = proc.stdout
    else:
        stdout = "<STDOUT logging skipped for this command>"

    return_code = proc.returncode
    status_msg = (
        "finished successful" if not return_code else "failed with non-zero code"
    )

    log_message = log_message.format(
        status=status_msg,
        cmd=cmd,
        stdout=stdout,
        stderr=proc.stderr,
        returncode=return_code,
    )

    if check_return_code and return_code:
        raise RuntimeError(log_exception(log_message))

    logger.info(log_message)

    return proc


def run_shell_cmd_as_process(
    cmd: str | list,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.STDOUT,
    encoding: str = "utf-8",
    **kwargs,
) -> str:
    """
    Function that wraps subprocess.Popen object.

    Execute provided function for GR related commands, print live logs and wait for result.

    Args:
        cmd: command to be executed
        stdout: standard output
        stderr: standard error file handles
        encoding: text mode for stdout and stderr
        kwargs: other subprocess.Popen keyword arguments
    Return:
        Command output
    """

    logger.info(f"Executing {cmd=}")
    output = ""

    with subprocess.Popen(
        cmd, shell=True, stdout=stdout, stderr=stderr, encoding=encoding, **kwargs
    ) as proc:
        for line in iter(proc.stdout.readline, b""):
            output += line
            if not line or proc.poll() is not None:
                break
            logger.info(f"STDOUT output is: {line.rstrip()}")
    return output


async def run_shell_cmd_as_process_async(
    cmd: str | list,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.STDOUT,
    encoding: str = "utf-8",
    **kwargs,
) -> str:
    """
    Function that wraps subprocess.Popen object.

    Execute provided function for GR related commands, print live logs and wait for result.

    Args:
        cmd: command to be executed
        stdout: standard output
        stderr: standard error file handles
        encoding: text mode for stdout and stderr
        kwargs: other subprocess.Popen keyword arguments
    Return:
        Command output
    """

    logger.info(f"Executing {cmd=}")
    with subprocess.Popen(
        cmd, shell=True, stdout=stdout, stderr=stderr, encoding=encoding, **kwargs
    ) as proc:
        while proc.poll() is None:
            await asyncio.sleep(5)
        output = proc.stdout.read()
    logger.info(f"Switchover STDOUT is: {output}")
    return output


def is_asyncio_task_alive(task_name: str) -> list:
    """
    Function that checks if asyncio task is still alive
    Returns:
        list with one element if task still alive or empty list if task completed
    """
    return list(filter(lambda task: task.get_name() == task_name, asyncio.all_tasks()))


def find_file(
    file_name: str,
    search_path: Path = ROOT_PATH,
    raise_exc: bool = False,
    exc_msg: str = "",
) -> Path | None:
    """
    Find file by file name
    Args:
        file_name: name of file
        search_path: start point to search the file
        raise_exc: raise FileNotFoundError exception if file is not found
        exc_msg: additional exception message to be printed in exception if it raised
    Raises:
        FileNotFoundError: when file is not found and raise_exc=True
    Returns:
        Path object if found otherwise None if raise=False
    """
    for file_path in search_path.glob("**/*"):
        if file_path.is_file() and file_path.name == file_name:
            return file_path
    if raise_exc:
        raise FileNotFoundError(
            f"{file_name=} is not found in {search_path}! {exc_msg}"
        )
    return None


def from_key_constructor(
    loader: yaml.Loader,
    node: yaml.Node,
    search_path: Path = ConfigFilePaths.CONFIG_FOLDER,
) -> None | str:
    """
    Custom YAML constructor to include a specific key from another YAML file.
    Usage in yaml file:
        !<tag_name> <file_name.yaml>:<key name>
    Args:
        loader: the YAML loader
        node: the YAML node containing the filename and key to include
        search_path: start folder for search include file, config folder by default
    Raises:
        ValueError: incorrect value provided for tag
        KeyError: if the specified key is not found in the included YAML file or
    Returns:
        value from specified key from the included YAML file
    """
    value = loader.construct_scalar(node)
    source_file_path = node.start_mark.name
    try:
        file_name, key = value.split(":")
    except ValueError as er:
        raise ValueError(
            f"Incorrect value provided for {node.tag} tag in {source_file_path} file: {value=}"
        ) from er

    file_path = find_file(
        file_name,
        search_path=search_path,
        raise_exc=True,
        exc_msg=f"Please check {source_file_path} file.",
    )

    with file_path.open(mode="r", encoding=UTF_8) as include_file:
        include_file_obj = yaml.load(include_file, Loader=yaml.FullLoader)
    try:
        return include_file_obj[key]
    except KeyError as er:
        raise KeyError(
            f"Key {key!r} is not found in {file_path.resolve()} include reference file "
            f"from {source_file_path=}!"
        ) from er


def get_ip_address_by_host(host: str) -> str:
    """Get current IP Address for provided host
    Args:
        host: host name
    Raises:
        ValueError: if incorrect host provided
    Returns:
        IP Address
    """
    try:
        return socket.gethostbyname(host)
    except socket.gaierror as err:
        raise ValueError(f"Incorrect host provided: {host=}") from err


def join_cmds(cmds_list: list) -> str:
    """Join console commands using '&&' as the separator
    Args:
        cmds_list: list with command that need to be joined
    Returns:
        string with joined commands
    """
    return " && ".join(cmds_list)


def compare_versions(
    current_version: str, target_version: str, comparator: str = ">="
) -> bool:
    """
    Compares two strings with versions
    Args:
        current_version: a current version to compare
        target_version: a target version to be compared with
        comparator: one of possible relational operators (>,<,>=,<=,==,!=)
    Returns:
        a result of the relational comparison
    """
    logger.info(f"Verifying if {current_version=} {comparator} {target_version=}")
    comparators = {
        ">": gt,
        ">=": ge,
        "<": lt,
        "<=": le,
        "==": eq,
        "!=": ne,
    }
    try:
        return comparators[comparator](
            version.parse(current_version), version.parse(target_version)
        )
    except KeyError as err:
        raise KeyError(
            f"Invalid comparator '{comparator}'. Please use one "
            f"from the list of possible {comparators.keys()}"
        ) from err


def create_file_from_template(
    template_path: Path, file_path: Path, content_dict: dict
) -> None:
    """
    Creates a file based on Jinja template populated with a specified content
    Args:
        template_path: A path to the template file
        file_path: A path to the file to be rendered
        content_dict: Data to populate the template with
    """
    logger.info(
        f"Creating a file {file_path} by rendering a template {template_path} "
        f"with a specified data:\n{content_dict}"
    )
    environment = Environment(loader=FileSystemLoader(template_path.parent))
    template = environment.get_template(template_path.name)
    content = template.render(content_dict)

    with file_path.open(mode="w", encoding=UTF_8) as f:
        f.write(content)
