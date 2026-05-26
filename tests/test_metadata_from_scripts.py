"""Tests for metadata inference from generated scripts."""

from __future__ import annotations

from pathlib import Path

from totvs_helper.services.metadata_from_scripts import infer_metadata_from_scripts
from totvs_helper.services.script_generator import GeneratedScripts

_EXPECTED = Path(__file__).resolve().parent / "expected"


def _load_scripts() -> GeneratedScripts:
    return GeneratedScripts(
        query_etl=(_EXPECTED / "query_etl.sql").read_text(encoding="utf-8"),
        ddl_create=(_EXPECTED / "ddl_create.sql").read_text(encoding="utf-8"),
        script_delete=(_EXPECTED / "script_delete.sql").read_text(encoding="utf-8"),
        script_update=(_EXPECTED / "script_update.sql").read_text(encoding="utf-8"),
        differential=(_EXPECTED / "differential.txt").read_text(encoding="utf-8"),
    )


def test_infer_fields_from_ddl_create() -> None:
    fields, pk_fields = infer_metadata_from_scripts(_load_scripts())
    names = [f.name for f in fields]
    assert "empresa" in names
    assert "id" in names
    assert "nome" in names
    assert "DATA_ALTERACAO" not in names
    assert pk_fields == ["id", "empresa"]
    nome = next(f for f in fields if f.name == "nome")
    assert nome.data_type == "character"
    assert nome.width == 10
