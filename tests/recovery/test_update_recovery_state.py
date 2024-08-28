"""Module that contains test function for verifying GR update recovery state procedure"""

from core_libs.eo.ccd.k8s_data.pods import (
    ERIC_GR_BUR_ORCH,
    ERIC_CNOM_SERVER,
)
from pytest import mark, fixture

from apps.codeploy.codeploy_app import CodeployApp
from apps.gr.data.constants import (
    GeoRecoveryStatuses,
    GrBurOrchestratorDeploymentEnvVars,
    GrTimeouts,
)
from apps.gr.geo_redundancy import GeoRedundancyApp


@fixture
def decrease_default_recovery_check_timeout(
    codeploy_app_passive_site: CodeployApp,
) -> None:
    """
    Change default timeout value for recovery pod checking
    """
    codeploy_app_passive_site.update_bur_orchestrator_deployment_env_variable(
        env_var=GrBurOrchestratorDeploymentEnvVars.POD_UP_STATE_TIMEOUT,
        value=str(GrTimeouts.RECOVERY_POD_CHECK_CUSTOM),
    )


@mark.update_recovery_state
def test_update_recovery_state(
    gr_app: GeoRedundancyApp,
    codeploy_app_passive_site: CodeployApp,
    decrease_default_recovery_check_timeout: None,  # pylint: disable=unused-argument
) -> None:
    """
    Preconditions that should be done before run the test:
    - Perform switchover operation when (old) Active Site (now Passive Site) was offline or unavailable

    This test performs and verifies following:
        1. breaks (scales in one of vital pod to 0) a Passive Site
        2. restores availability for the Passive Site
        3. verifies the Passive Site has RECOVERY_IN_PROGRESS status (under discussion)
        4. verifies the Passive Site gets NOT_RECOVERABLE status
        5. fixes the Passive Site
        6. performs update-recovery-state DM command
        7. verifies the Passive Site gets RECOVERABLE status
    """
    # break a Passive Site
    codeploy_app_passive_site.change_deployment_replicas(ERIC_CNOM_SERVER, replicas=0)

    # make the Passive Site available
    codeploy_app_passive_site.change_deployment_replicas(ERIC_GR_BUR_ORCH, replicas=1)

    # uncomment or remove the following assert according to result of EO-172212:

    # assert gr_app.verify_recovery_status(
    #     GeoRecoveryStatuses.RECOVERY_IN_PROGRESS,
    # ), f"Recovery Status not in {GeoRecoveryStatuses.RECOVERY_IN_PROGRESS} state"

    assert gr_app.verify_recovery_status(
        GeoRecoveryStatuses.NOT_RECOVERABLE,
        timeout=GrTimeouts.RECOVERY_POD_CHECK_CUSTOM + 60,
    ), f"Recovery Status not in {GeoRecoveryStatuses.NOT_RECOVERABLE} state"

    # fix the Passive Site
    codeploy_app_passive_site.k8s_eo_client.scale_deployment_replicas(
        pod=ERIC_CNOM_SERVER, replicas=1
    )

    assert gr_app.update_site_recovery_status(), "Recovery State Update has been failed"

    assert gr_app.verify_recovery_status(
        GeoRecoveryStatuses.RECOVERABLE,
    ), f"Recovery Status not in {GeoRecoveryStatuses.RECOVERABLE} state"
