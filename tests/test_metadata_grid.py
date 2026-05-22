"""Tests for metadata grid row building."""

from __future__ import annotations


def test_set_metadata_builds_rows() -> None:
    fields = [
        ("id", "integer", 4, 0, "integer"),
        ("nome", "varchar", 40, 0, "string"),
    ]
    pk_fields = ["id"]

    rows = []
    pk_set = {str(name) for name in pk_fields}
    for field in fields:
        name = str(field[0])
        rows.append(
            (
                name,
                str(field[1]),
                str(field[2]),
                str(field[3]),
                str(field[4]),
                "sim" if name in pk_set else "",
            )
        )

    assert len(rows) == 2
    assert rows[0][0] == "id"
    assert rows[0][5] == "sim"
    assert rows[1][5] == ""
