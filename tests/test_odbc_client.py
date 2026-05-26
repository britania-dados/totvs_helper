from unittest.mock import Mock

import pyodbc
import pytest

from totvs_helper.config.settings import Settings
from totvs_helper.errors import OdbcConnectionError
from totvs_helper.infra.odbc_client import FieldMeta, OdbcClient, select_fields_for_sample


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        odbc_user_primary="u1",
        odbc_password_primary="p1",
        odbc_user_fallback="u2",
        odbc_password_fallback="p2",
        odbc_timeout_seconds=1,
    )


def test_list_odbcs_sorted_alphabetically(monkeypatch):
    monkeypatch.setattr(
        pyodbc,
        "dataSources",
        lambda: {
            "EMS2UNIT_ELETRO": "OpenEdge 11.7 Driver",
            "MOV2UNIT_BRIC": "OpenEdge 11.7 Driver",
            "AAA_TEST": "OpenEdge 11.7 Driver",
            "OTHER": "SQL Server",
        },
    )

    names = OdbcClient.list_odbcs()

    assert names == ["AAA_TEST", "EMS2UNIT_ELETRO", "MOV2UNIT_BRIC"]


def test_connect_uses_primary_credentials(settings, monkeypatch):
    connection_mock = Mock()
    connect_mock = Mock(return_value=connection_mock)
    monkeypatch.setattr(pyodbc, "connect", connect_mock)

    client = OdbcClient(settings)
    result = client.connect("totvs_dsn")

    assert result is connection_mock
    called_conn_string = connect_mock.call_args.kwargs.get("connection_string")
    if called_conn_string is None:
        called_conn_string = connect_mock.call_args.args[0]
    assert "Uid=u1" in called_conn_string


def test_select_fields_for_sample_skips_blob_and_prioritizes_pk() -> None:
    fields = [
        FieldMeta("logo", "blob", 0, 0, "blob"),
        FieldMeta("cod-emitente", "integer", 4, 0, "integer"),
        FieldMeta("nome-abrev", "character", 24, 0, "varchar"),
    ]
    selected = select_fields_for_sample(fields, ["cod-emitente"])
    names = [field.name for field in selected]
    assert "logo" not in names
    assert names[0] == "cod-emitente"
    assert "nome-abrev" in names


def test_fetch_sample_rows_builds_query(settings, monkeypatch):
    connection = Mock()
    cursor = Mock()
    cursor.fetchall.return_value = [(1, "x")]
    connection.cursor.return_value = cursor

    fields = [
        FieldMeta("col-a", "char", 10, 0, "string"),
        FieldMeta("col-b", "int", 4, 0, "integer"),
        FieldMeta("anexo", "blob", 0, 0, "blob"),
    ]
    client = OdbcClient(settings)
    columns, rows = client.fetch_sample_rows(
        "my-table",
        fields,
        connection,
        pk_fields=["col-b"],
        limit=10,
    )

    assert columns == ["col-b", "col-a"]
    assert '"col-a"' in cursor.execute.call_args.args[0]
    assert '"col-b"' in cursor.execute.call_args.args[0]
    assert rows == [(1, "x")]
    executed = cursor.execute.call_args.args[0]
    assert "TOP 10" in executed
    assert 'PUB."my-table"' in executed
    cursor.close.assert_called_once()


def test_fetch_sample_rows_with_offset(settings):
    connection = Mock()
    cursor = Mock()
    cursor.fetchall.return_value = []
    connection.cursor.return_value = cursor

    fields = [FieldMeta("col-a", "char", 10, 0, "string")]
    client = OdbcClient(settings)
    client.fetch_sample_rows(
        "my-table",
        fields,
        connection,
        limit=10,
        offset=20,
    )

    executed = cursor.execute.call_args.args[0]
    assert "TOP 30" in executed
    assert "SKIP" not in executed


def test_connect_fallback_after_primary_failure(settings, monkeypatch):
    connection_mock = Mock()
    connect_mock = Mock(
        side_effect=[
            pyodbc.Error("primary failed"),
            connection_mock,
        ]
    )
    monkeypatch.setattr(pyodbc, "connect", connect_mock)

    client = OdbcClient(settings)
    result = client.connect("totvs_dsn")

    assert result is connection_mock
    assert connect_mock.call_count == 2


def test_connect_raises_when_all_attempts_fail(settings, monkeypatch):
    connect_mock = Mock(side_effect=pyodbc.Error("all failed"))
    monkeypatch.setattr(pyodbc, "connect", connect_mock)
    client = OdbcClient(settings)

    with pytest.raises(OdbcConnectionError):
        client.connect("totvs_dsn")
