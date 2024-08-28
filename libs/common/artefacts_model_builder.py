"""Module with ArtefactsBuilder class"""

from dataclasses import dataclass

from core_libs.common.constants import ArtefactConfigKeys, ArtefactAppType
from core_libs.common.custom_exceptions import ConfigurationNotFoundException
from apps.cvnfm.data.cvnfm_artefact_model import CvnfmArtifactModel
from apps.vmvnfm.data.vmvnfm_artefact_model import VmvnfmArtefactModel
from libs.utils.logging.logger import log_exception, logger

REQUIRED_PARAM_MISSING = "Mandatory parameter {} is missing in artefact config"


class ArtefactsBuilder:
    """
    Class for build artefact models by artefact type from config
    """

    def __init__(self, config_artefacts: dict):
        self._config_artefacts = config_artefacts

    def get_by_id(self, artefact_id: str) -> dataclass:
        """
        Get artefact by its id

        Returns:
            dataclass object
        """
        logger.debug(f"Searching artefact by {artefact_id=}")
        return self._build_model_for_artefact_by_id(artefact_id)

    def _build_model_for_artefact_by_id(
        self,
        artefact_id: str,
    ) -> CvnfmArtifactModel | VmvnfmArtefactModel:
        """Method for build artefacts in model view using config artefacts
        Args:
            artefact_id: artefact id
        Returns:
            dict with artefact models
        """

        for id_, artefact in self._config_artefacts.items():
            if id_ == artefact_id:
                artifact_model = self._build_model(artefact)
                return artifact_model

        raise ConfigurationNotFoundException(
            log_exception(f"Package {artefact_id=} is not found in config")
        )

    def _build_model(self, artefact: dict) -> CvnfmArtifactModel | VmvnfmArtefactModel:
        """Method for build artefact model by artefact type using artefact config
        Args:
            artefact: artefact from config
        Raises:
            KeyError: for incorrect artefact app type
        Returns:
            artefact dataclass or list with artefact dataclasses
        """
        artefact_type = artefact.get(ArtefactConfigKeys.APPLICATION_TYPE)
        try:
            model = {
                ArtefactAppType.CVNFM: self._build_cvnfm_model,
                ArtefactAppType.VMVNFM: self._build_vmvnfm_model,
            }[artefact_type](artefact)

        except KeyError as err:
            raise KeyError(
                log_exception(f"Incorrect artefact type: {artefact_type}")
            ) from err

        return model

    @staticmethod
    def _build_cvnfm_model(artefact: dict) -> CvnfmArtifactModel:
        """Method for build CvnfmArtifactModel object
        Args:
            artefact: artefact from config
        Raises:
            ConfigurationNotFoundException: when a mandatory parameter is missing
        Returns:
            dataclass object
        """
        try:
            return CvnfmArtifactModel(
                url=artefact[ArtefactConfigKeys.PACKAGE_PATH],
                onboarding_timeout=artefact.get(
                    ArtefactConfigKeys.PACKAGE_ONBOARDING_TIMEOUT
                ),
                lcm_timeout=artefact.get(ArtefactConfigKeys.LCM_OPERATION_TIMEOUT),
                additional_config=artefact.get(
                    ArtefactConfigKeys.ADDITIONAL_CONFIG_PATH
                ),
                additional_config_modify=artefact.get(
                    ArtefactConfigKeys.ADDITIONAL_CONFIG_PATH_FOR_CHANGE
                ),
                additional_config_scale=artefact.get(
                    ArtefactConfigKeys.ADDITIONAL_CONFIG_PATH_FOR_SCALE
                ),
                actions=artefact.get(ArtefactConfigKeys.ACTIONS),
                descriptor_id=artefact.get(ArtefactConfigKeys.DESCRIPTOR_ID),
            )
        except KeyError as err:
            raise ConfigurationNotFoundException(
                log_exception(REQUIRED_PARAM_MISSING.format(err))
            ) from err

    @staticmethod
    def _build_vmvnfm_model(artefact: dict) -> VmvnfmArtefactModel:
        """Method for build VmvnfmArtefactModel object
        Args:
            artefact: artefact from config
        Raises:
            ConfigurationNotFoundException: when a mandatory parameter is missing
        Returns:
            dataclass object
        """
        try:
            return VmvnfmArtefactModel(
                url=artefact[ArtefactConfigKeys.PACKAGE_PATH],
                srt_ram=artefact.get(ArtefactConfigKeys.SRT_RAM),
                srt_cpu=artefact.get(ArtefactConfigKeys.SRT_CPU),
                srt_disc_size=artefact.get(ArtefactConfigKeys.SRT_DISC_SIZE),
                descriptor_id=artefact.get(ArtefactConfigKeys.DESCRIPTOR_ID),
            )
        except KeyError as err:
            raise ConfigurationNotFoundException(
                log_exception(REQUIRED_PARAM_MISSING.format(err))
            ) from err
