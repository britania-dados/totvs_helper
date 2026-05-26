"""Rebuild column metadata from generated SQL (history without ODBC cache)."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.services.script_generator import GeneratedScripts

_SKIP_COLUMNS = frozenset({"DATA_ALTERACAO"})

_DDL_COLUMN_RE = re.compile(
    r"^\s+\[(?P<name>[^\]]+)\]\s+\[(?P<sqltype>[^\]]+)\]"
    r"(?:\((?P<args>[^\)]*)\))?",
    re.MULTILINE | re.IGNORECASE,
)

_PK_BLOCK_RE = re.compile(
    r"PRIMARY\s+KEY\s*\((.*?)\)\s*\)",
    re.DOTALL | re.IGNORECASE,
)


def infer_metadata_from_scripts(
    scripts: GeneratedScripts,
) -> Tuple[List[FieldMeta], List[str]]:
    """Parse DDL CREATE produced by ScriptGenerator to recover FieldMeta and PK."""
    ddl = scripts.ddl_create.strip()
    if not ddl:
        return [], []

    fields: List[FieldMeta] = []
    for match in _DDL_COLUMN_RE.finditer(ddl):
        name = match.group("name")
        if name in _SKIP_COLUMNS:
            continue
        fields.append(
            _field_meta_from_sql_type(
                name, match.group("sqltype"), match.group("args")
            )
        )

    pk_fields = _parse_pk_fields(ddl)
    if not pk_fields and fields:
        pk_fields = [fields[0].name]

    return fields, pk_fields


def _parse_pk_fields(ddl: str) -> List[str]:
    block = _PK_BLOCK_RE.search(ddl)
    if not block:
        return []
    return re.findall(r"\[([^\]]+)\]", block.group(1))


def _field_meta_from_sql_type(
    name: str, sqltype: str, args: Optional[str]
) -> FieldMeta:
    kind = sqltype.lower()
    arg = (args or "").strip()

    if kind in ("varchar", "nvarchar", "char", "nchar"):
        width = int(arg) if arg.isdigit() else 255
        return FieldMeta(name, "character", width, 0, "varchar")
    if kind == "integer":
        return FieldMeta(name, "integer", 17, 2, "integer")
    if kind in ("numeric", "decimal"):
        parts = [p.strip() for p in arg.split(",")] if arg else ["17", "2"]
        width = int(parts[0]) if parts and parts[0].isdigit() else 17
        decimals = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return FieldMeta(name, "decimal", width, decimals, kind)
    if kind in ("datetime2", "datetime", "timestamp", "date"):
        return FieldMeta(name, "date", 0, 0, "datetime")
    if kind == "bit":
        return FieldMeta(name, "logical", 0, 0, "bit")
    if kind == "varbinary":
        return FieldMeta(name, "character", 0, 0, "varbinary")
    return FieldMeta(name, "character", 255, 0, kind)
