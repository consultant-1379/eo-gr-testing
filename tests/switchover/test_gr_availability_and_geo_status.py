"""This module contains tests related to Geographical Redundancy Availability and Status functionality"""

from pytest import mark

from apps.gr.geo_redundancy import GeoRedundancyApp


@mark.gr_availability_and_status
def test_verify_gr_availability_and_status(
    gr_app: GeoRedundancyApp,
) -> None:
    """
    Verify Geographical Redundancy Availability and Status

    Args:
        gr_app: GeoRedundancyApp instance
    """
    is_gr_availability = gr_app.verify_gr_availability()
    assert (
        is_gr_availability
    ), "EO GR hasn't become available after the switchover operation"

    is_geo_status_success = gr_app.gr_status.make_and_verify_geo_status_command()
    assert (
        is_geo_status_success
    ), "GR Status command contains missmatch for performing switchover"
