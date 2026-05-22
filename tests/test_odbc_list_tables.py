"""Tests for ODBC table listing helpers."""

from __future__ import annotations

from unittest.mock import Mock

from totvs_helper.infra.odbc_client import OdbcClient


def test_normalize_rowid_from_bytes() -> None:
    assert OdbcClient._normalize_rowid(b"abc") == "abc"


def test_normalize_rowid_from_string() -> None:
    assert OdbcClient._normalize_rowid("000123") == "000123"


def test_store_table_rows_skips_blank_names() -> None:
    client = OdbcClient(Mock())
    names = client._store_table_rows([("item", b"rid1"), ("", b"rid2"), ("  ", b"3")])
    assert names == ["item"]
    assert client.get_table_recid("item") == "rid1"


def test_list_tables_falls_back_to_catalog(monkeypatch) -> None:
    client = OdbcClient(Mock())
    connection = Mock()
    cursor = Mock()
    cursor.fetchall.return_value = []
    catalog_row = Mock()
    catalog_row.table_schem = "PUB"
    catalog_row.table_name = "cad-item"
    cursor.tables.return_value = [catalog_row]
    connection.cursor.return_value = cursor

    tables = client.list_tables(connection)

    assert tables == ["cad-item"]
    assert client.get_table_recid("cad-item") == ""
