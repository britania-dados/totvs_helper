"""SQL builders for Pentaho Table Input steps."""

from __future__ import annotations

from typing import List, Optional

from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.services.constants import filter_fields
from totvs_helper.services.ecom_emitente_keys import (
    map_ecom_emitente_pentaho_projection,
)
from totvs_helper.services.pentaho.constants import detect_source_family

__all__ = [
    "build_pentaho_table_input_sql",
    "detect_source_family",
    "escape_xml_text",
    "format_entity_name",
]


def format_entity_name(progress_table: str) -> str:
    """Progress table name to PascalCase entity (tot destination)."""
    return progress_table.title().replace("-", "")


def escape_xml_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pentaho_table_input_sql(
    selected_table: str,
    fields: List[FieldMeta],
    include_free_fields: bool,
    *,
    empresa_code: Optional[str] = None,
    base_code: Optional[str] = None,
    ecom_source: bool = False,
) -> str:
    """Build SELECT for Pentaho (lowercase style, pub schema)."""
    filtered = filter_fields(fields, include_free_fields)
    lines: List[str] = []
    if empresa_code is not None:
        lines.append(f"    '{empresa_code}' \"EMPRESA\"")
    elif base_code is not None:
        lines.append(f"    '{base_code}' \"BASE\"")

    for field in filtered:
        lines.append(
            _map_pentaho_projection(
                field,
                selected_table=selected_table,
                ecom_source=ecom_source,
            )
        )

    body = ", \n".join(lines)
    table = selected_table.lower()
    return f"select \n{body}\nfrom pub.\"{table}\" with (nolock)"


def _map_pentaho_projection(
    field: FieldMeta,
    *,
    selected_table: str,
    ecom_source: bool,
) -> str:
    ecom_line = map_ecom_emitente_pentaho_projection(
        field, progress_table=selected_table, ecom_source=ecom_source
    )
    if ecom_line is not None:
        return ecom_line
    if field.data_type == "character":
        return f'    substring("{field.name}",1,{field.width}) "{field.name}"'
    if field.data_type == "date":
        return (
            "    case \n"
            f'          when "{field.name}"  < \'12/31/9999\' and "{field.name}" > '
            f"'01/01/1900' then CONVERT ( 'date',\"{field.name}\") \n"
            f'          when "{field.name}"  <= \'01/01/1900\' then \'01/01/1900\' \n'
            f'          when "{field.name}"  >= \'12/31/9999\' then \'12/31/9999\' \n'
            f'    end "{field.name}"'
        )
    if field.data_type == "logical":
        return (
            f"    CONVERT('bit', CASE WHEN \"{field.name}\" <> '1' THEN '0' "
            f"ELSE '1' END) \"{field.name}\""
        )
    return f'    "{field.name}"'
