"""Module to store test function that makes switchover with available backup id"""
from typing import Generator

from pytest import mark

from apps.gr.geo_redundancy import GeoRedundancyApp

# pylint: disable=unused-argument

pytestmark = [mark.switchover_with_available_backup_id]


def test_decrease_backup_cycle_interval_and_check_new_backup_created(
    decrease_backup_cycle_interval_and_check_new_backup_created: None,
) -> None:
    """
    The purpose of this test call fixture that changes default interval value for creating backup on both sites,
    in order to prevent making switchover with backup which does not contain the most recent data.
    It checks if backup is updated in availability cmd to the new one.
    Args:
        decrease_backup_cycle_interval_and_check_new_backup_created: decrease backup interval and
                                                                    check new backup created
    """
    assert (
        decrease_backup_cycle_interval_and_check_new_backup_created
    ), "Backup is not updated"


@mark.switchover_with_available_backup_id_without_backup_update_check
def test_make_switchover_with_available_backup_id(
    gr_app: GeoRedundancyApp,
    healthcheck_two_sites_switchover_success: Generator,
) -> None:
    """
    Test does the following:
    - make and verify GR Status command
    - make and verify GR Availability command
    - get backup ID from availability command output
    - make switchover with this backup ID

    Args:
        gr_app: GeoRedundancyApp instance
        healthcheck_two_sites_switchover_success: CodeployApp instance with passive site config
    """
    assert (
        gr_app.verify_gr_availability()
    ), "EO GR hasn't become available after the switchover operation"
    assert (
        gr_app.gr_status.make_and_verify_geo_status_command()
    ), "GR Status command contains missmatch for performing switchover"

    backup_id = gr_app.get_backup_id_from_availability()

    assert gr_app.make_and_verify_switchover(
        backup_id=backup_id
    ), f"Switchover with {backup_id=} completed with errors"
