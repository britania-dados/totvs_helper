"""Tests for alternating row stripes grouped by index name."""

from __future__ import annotations

from totvs_helper.ui.widgets.sample_data_grid import SampleDataGrid


def test_stripe_tags_alternate_per_index_group() -> None:
    groups = ["A", "A", "B", "B", "C", "D", "D", "D", "E"]
    tags = SampleDataGrid.stripe_tags_for_groups(groups)

    assert tags == [
        "stripe_even",
        "stripe_even",
        "stripe_odd",
        "stripe_odd",
        "stripe_even",
        "stripe_odd",
        "stripe_odd",
        "stripe_odd",
        "stripe_even",
    ]
