"""
    This module contains dummy test cases to test single GR functions
    Please use it only in case of test needs!
"""
from pytest import mark
from apps.gr.geo_redundancy import GeoRedundancyApp


@mark.dummy_gr_availability
def test_dummy_gr_availability(gr_app: GeoRedundancyApp):
    """
    Make Geographical Redundancy Availability
    Args:
        gr_app: GeoRedundancyApp instance
    """
    assert gr_app.verify_gr_availability()


@mark.dummy_gr_status
def test_dummy_gr_status(gr_app: GeoRedundancyApp):
    """
    Make Geographical Redundancy Status
    Args:
        gr_app: GeoRedundancyApp instance
    """
    assert gr_app.gr_status.make_and_verify_geo_status_command()


@mark.dummy_gr_switchover
def test_dummy_gr_switchover(gr_app: GeoRedundancyApp):
    """
    Make Geographical Redundancy
    Args:
        gr_app: GeoRedundancyApp instance
    """
    assert gr_app.make_and_verify_switchover()
