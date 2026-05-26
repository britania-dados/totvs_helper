"""Tests for ECOM emitente stage key transforms."""

from tests.conftest import field
from totvs_helper.services.ecom_emitente_keys import (
    map_ecom_emitente_etl_projection,
    map_ecom_emitente_pentaho_projection,
)
from totvs_helper.services.script_generator import ScriptGenerator
from totvs_helper.services.pentaho_sql import build_pentaho_table_input_sql


def test_ecom_emitente_cod_and_nome_abrev() -> None:
    fields = [
        field("cod-emitente", data_type="integer", fetch_datatype="integer"),
        field("nome-abrev", width=30),
        field("nome", width=40),
    ]
    sql = build_pentaho_table_input_sql(
        "emitente",
        fields,
        include_free_fields=True,
        base_code="ECOM",
        ecom_source=True,
    )
    assert '(1000000000 + "cod-emitente")' in sql
    assert '\'E_\' + substring("nome-abrev", 1, 24)' in sql
    assert 'substring("nome",1,40)' in sql


def test_ecom_emitente_skipped_for_varejo() -> None:
    fields = [field("cod-emitente", data_type="integer", fetch_datatype="integer")]
    sql = build_pentaho_table_input_sql(
        "emitente",
        fields,
        include_free_fields=True,
        base_code="VAREJO",
        ecom_source=False,
    )
    assert "1000000000" not in sql
    assert '"cod-emitente"' in sql


def test_ecom_transform_only_emitente_table() -> None:
    line = map_ecom_emitente_pentaho_projection(
        field("cod-emitente", data_type="integer", fetch_datatype="integer"),
        progress_table="comprador",
        ecom_source=True,
    )
    assert line is None


def test_ecom_emitente_etl_query() -> None:
    fields = [
        field("cod-emitente", data_type="integer", fetch_datatype="integer"),
        field("nome-abrev", width=30),
    ]
    scripts = ScriptGenerator().generate_helpers(
        include_free_fields=True,
        multi_company=True,
        selected_table="emitente",
        fields=fields,
        pk_fields=["cod-emitente"],
        ecom_keys=True,
    )
    assert "(1000000000 + \"cod-emitente\") AS \"cod-emitente\"" in scripts.query_etl
    assert '\'E_\' + SUBSTRING("nome-abrev", 1, 24) AS "nome-abrev"' in scripts.query_etl
    assert "(1000000000" not in scripts.ddl_create


def test_ecom_emitente_etl_projection_helper() -> None:
    line = map_ecom_emitente_etl_projection(
        field("nome-abrev", width=30),
        progress_table="emitente",
        ecom_keys=True,
    )
    assert line is not None
    assert "SUBSTRING" in line
    assert "AS \"nome-abrev\"" in line
