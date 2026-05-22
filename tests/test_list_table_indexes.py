"""Tests for OpenEdge index listing."""

from __future__ import annotations

from unittest.mock import Mock

import pyodbc

from totvs_helper.config.settings import Settings
from totvs_helper.infra.odbc_client import OdbcClient


def _client() -> OdbcClient:
    return OdbcClient(
        Settings(
            odbc_user_primary="u",
            odbc_password_primary="p",
            odbc_user_fallback="u2",
            odbc_password_fallback="p2",
            odbc_timeout_seconds=1,
        )
    )


def test_list_table_indexes_maps_unique_and_primary() -> None:
    connection = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = (None,)
    cursor.fetchall.return_value = [
        ("idx_pk", 1, 1, "id"),
        ("idx_pk", 1, 2, "code"),
        ("idx_name", 0, 1, "name"),
    ]
    connection.cursor.return_value = cursor

    rows = _client().list_table_indexes(
        "rec-1", connection, pk_fields=["id", "code"]
    )

    assert len(rows) == 3
    pk_rows = [r for r in rows if r.index_name == "idx_pk"]
    assert all(r.is_unique for r in pk_rows)
    assert all(r.is_primary for r in pk_rows)
    name_row = next(r for r in rows if r.index_name == "idx_name")
    assert not name_row.is_unique
    assert not name_row.is_primary


def test_list_table_indexes_tries_next_query_when_first_returns_empty() -> None:
    connection = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = (None,)
    cursor.fetchall.side_effect = [
        [],
        [("idx_a", 1, "col1")],
    ]
    connection.cursor.return_value = cursor

    rows = _client().list_table_indexes("rec-1", connection)

    assert len(rows) == 1
    assert rows[0].index_name == "idx_a"
    assert cursor.execute.call_count == 3


def test_list_table_indexes_fallback_without_index_seq_column() -> None:
    connection = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = (None,)

    def execute_side_effect(sql: str, _recid: str) -> None:
        if "_index-seq" in sql:
            raise pyodbc.Error("column _index-seq not found")

    cursor.execute.side_effect = execute_side_effect
    cursor.fetchall.return_value = [
        ("idx_pk", 1, "id"),
        ("idx_pk", 1, "code"),
    ]
    connection.cursor.return_value = cursor

    rows = _client().list_table_indexes(
        "rec-1", connection, pk_fields=["id", "code"]
    )

    assert len(rows) == 2
    assert rows[0].is_primary


def test_list_table_indexes_marks_primary_from_prime_index_recid() -> None:
    connection = Mock()
    cursor = Mock()
    cursor.fetchone.return_value = ("prime-1",)
    cursor.fetchall.side_effect = [
        [],
        [],
        [],
        [],
        [],
        [
            ("idx_pk", 1, 1, "id", "prime-1"),
            ("idx_other", 0, 1, "name", "other-9"),
        ],
    ]
    connection.cursor.return_value = cursor

    rows = _client().list_table_indexes("rec-1", connection, pk_fields=[])

    pk_row = next(r for r in rows if r.index_name == "idx_pk")
    other_row = next(r for r in rows if r.index_name == "idx_other")
    assert pk_row.is_primary
    assert not other_row.is_primary
