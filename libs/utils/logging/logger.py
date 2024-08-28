"""
File for customize logging
"""

import logging.config
import os
import yaml

from core_libs.common.constants import EnvVariables
from libs.common.constants import LoggingConfigPath, EO_GR_LOGGER_NAME, UTF_8

# Read logging configuration from YAML file
with LoggingConfigPath.LOGGING_CONFIG.open(encoding=UTF_8) as ymlfile:
    logging_settings = yaml.load(ymlfile, Loader=yaml.FullLoader)

# Update logging configuration with a filename for a 'file_hdlr' handler
logs_folder = os.getenv(EnvVariables.LOGS_FOLDER, "")
log_filename = os.getenv(EnvVariables.LOG_FILENAME, "log.log")
log_path = os.path.join(logs_folder, log_filename)
logging_settings["handlers"]["file_hdlr"]["filename"] = log_path

# Create 'eo_gr' logger
logger = logging.getLogger(EO_GR_LOGGER_NAME)
logging.config.dictConfig(logging_settings)

# Setup log level by environment variable LOG_LEVEL for all loggers
log_level = os.getenv(EnvVariables.LOG_LEVEL, "DEBUG")
if log_level.isdigit():
    log_level = logging.getLevelName(int(log_level))

logger.setLevel(log_level)
logging.getLogger("core_libs").setLevel(log_level)
logging.getLogger("root").setLevel(log_level)


def log_exception(error_message):
    """
    Method allows to log the exception in the log
    :param error_message: the exception text
    :type error_message: str
    :return: the exception text
    :rtype: str
    """
    logger.exception(msg=error_message)
    return error_message


def set_eo_gr_logger_for_class(class_instance: object) -> logging.Logger:
    """
    Create new logger with class name of provided instance, and inheriting from EO GR logger
    Args:
        class_instance: class instance
    Returns:
        new logger object with class name of provided instance
    """
    return logging.getLogger(
        f"{EO_GR_LOGGER_NAME}.[{class_instance.__class__.__name__}]"
    )
