"""Module to store EO RV Node related data"""


class EoNodePaths:
    """Class that contains EO RV Node base paths"""

    WORK_DIRS = "/eo/workdir/"
    WORK_DIR = WORK_DIRS + "workdir_{env_name}/"
    LM_WORK_DIR = WORK_DIRS + "workdir_lm_{env_name}/"
    LOG_DIR = WORK_DIR + "logs/"
    LM_WORK_DIR_KUBE_CONFIG = LM_WORK_DIR + "kube_config/config"
