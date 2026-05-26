"""ECOM-specific stage key transforms for emitente (Pentaho and future SSIS).

Varejo and ECOM maintain separate emitente master data; the same cod-emitente can
exist in both bases. Stage loads therefore remap keys only for the ECOM source.
"""

from __future__ import annotations

from typing import Optional

from totvs_helper.infra.odbc_client import FieldMeta

EMITENTE_PROGRESS_TABLE = "emitente"
COD_EMITENTE_FIELD = "cod-emitente"
NOME_ABREV_FIELD = "nome-abrev"
ECOM_COD_EMITENTE_OFFSET = 1_000_000_000

__all__ = [
    "COD_EMITENTE_FIELD",
    "ECOM_COD_EMITENTE_OFFSET",
    "EMITENTE_PROGRESS_TABLE",
    "NOME_ABREV_FIELD",
    "is_emitente_table",
    "map_ecom_emitente_etl_projection",
    "map_ecom_emitente_pentaho_projection",
]


def is_emitente_table(progress_table: str) -> bool:
    return (progress_table or "").strip().lower() == EMITENTE_PROGRESS_TABLE


def map_ecom_emitente_etl_projection(
    field: FieldMeta,
    *,
    progress_table: str,
    ecom_keys: bool,
) -> Optional[str]:
    """Query ETL projection for ECOM emitente keys, or None for default mapping."""
    if not ecom_keys or not is_emitente_table(progress_table):
        return None
    if field.name == COD_EMITENTE_FIELD:
        return (
            f'    ({ECOM_COD_EMITENTE_OFFSET} + "{field.name}") AS "{field.name}"'
        )
    if field.name == NOME_ABREV_FIELD:
        return (
            f'    \'E_\' + SUBSTRING("{field.name}", 1, 24) AS "{field.name}"'
        )
    return None


def map_ecom_emitente_pentaho_projection(
    field: FieldMeta,
    *,
    progress_table: str,
    ecom_source: bool,
) -> Optional[str]:
    """OpenEdge projection for ECOM emitente keys, or None for default mapping."""
    if not ecom_source or not is_emitente_table(progress_table):
        return None
    if field.name == COD_EMITENTE_FIELD:
        return f'    ({ECOM_COD_EMITENTE_OFFSET} + "{field.name}") "{field.name}"'
    if field.name == NOME_ABREV_FIELD:
        return f'    \'E_\' + substring("{field.name}", 1, 24) "{field.name}"'
    return None
