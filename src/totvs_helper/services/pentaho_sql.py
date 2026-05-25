"""SQL builders for Pentaho Table Input steps."""

from __future__ import annotations

from typing import List, Optional, Sequence

from totvs_helper.services.constants import FREE_FIELDS_TO_IGNORE
from totvs_helper.services.pentaho_constants import detect_source_family

__all__ = ["build_pentaho_table_input_sql", "detect_source_family", "escape_xml_text", "format_entity_name"]


def format_entity_name(progress_table: str) -> str:
    """Progress table name to PascalCase entity (tot destination)."""
    return progress_table.title().replace("-", "")


def escape_xml_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pentaho_table_input_sql(
    selected_table: str,
    fields: List[Sequence],
    include_free_fields: bool,
    *,
    empresa_code: Optional[str] = None,
    base_code: Optional[str] = None,
) -> str:
    """Build SELECT for Pentaho (lowercase style, pub schema)."""
    filtered = [
        field
        for field in fields
        if include_free_fields or field[0] not in FREE_FIELDS_TO_IGNORE
    ]
    lines: List[str] = []
    if empresa_code is not None:
        lines.append(f"    '{empresa_code}' \"EMPRESA\"")
    elif base_code is not None:
        lines.append(f"    '{base_code}' \"BASE\"")

    for field in filtered:
        lines.append(_map_pentaho_projection(field))

    body = ", \n".join(lines)
    table = selected_table.lower()
    return f"select \n{body}\nfrom pub.\"{table}\" with (nolock)"


def _map_pentaho_projection(field: Sequence) -> str:
    field_name = field[0]
    data_type = field[1]
    width = field[2]

    if data_type == "character":
        return f'    substring("{field_name}",1,{width}) "{field_name}"'
    if data_type == "date":
        return (
            "    case \n"
            f'          when "{field_name}"  < \'12/31/9999\' and "{field_name}" > '
            f"'01/01/1900' then CONVERT ( 'date',\"{field_name}\") \n"
            f'          when "{field_name}"  <= \'01/01/1900\' then \'01/01/1900\' \n'
            f'          when "{field_name}"  >= \'12/31/9999\' then \'12/31/9999\' \n'
            f'    end "{field_name}"'
        )
    if data_type == "logical":
        return (
            f"    CONVERT('bit', CASE WHEN \"{field_name}\" <> '1' THEN '0' "
            f"ELSE '1' END) \"{field_name}\""
        )
    return f'    "{field_name}"'
