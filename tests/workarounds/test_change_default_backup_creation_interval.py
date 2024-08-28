"""Workaround for https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/EO-172689"""
from pytest import mark

# pylint: disable=unused-argument


@mark.workaround_change_backup_interval
def test_workaround_change_backup_interval(
    decrease_backup_cycle_interval_on_both_sites: None,
):
    """Workaround for https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/EO-172689"""
