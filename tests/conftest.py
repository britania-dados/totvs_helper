"""Shared test helpers."""

from totvs_helper.infra.odbc_client import FieldMeta


def field(
    name: str,
    data_type: str = "character",
    width: int = 10,
    decimals: int = 0,
    fetch_datatype: str = "varchar",
) -> FieldMeta:
    return FieldMeta(name, data_type, width, decimals, fetch_datatype)
