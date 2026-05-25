"""Tests for Pentaho SQL helpers."""

from totvs_helper.services.pentaho_constants import (
    DEFAULT_INCLUDE_FREE_FIELDS,
    is_multi_company_dsn,
)
from totvs_helper.services.pentaho_sql import (
    build_pentaho_table_input_sql,
    detect_source_family,
    format_entity_name,
)


def test_detect_source_family_from_dsn() -> None:
    assert detect_source_family("EMS2UNIT_ELETRO") == "ems2unit"
    assert detect_source_family("MOV2UNIT_BRIC") == "mov2unit"
    assert detect_source_family("ESP2UNIT_MANAUS") == "esp2unit"
    assert detect_source_family("ESP2CORP") == "esp2corp"
    assert detect_source_family("WMS_VAREJO") == "wms"


def test_multi_company_default_from_dsn() -> None:
    assert DEFAULT_INCLUDE_FREE_FIELDS is True
    assert is_multi_company_dsn("EMS2UNIT_ELETRO") is True
    assert is_multi_company_dsn("MOV2UNIT_BRIC") is True
    assert is_multi_company_dsn("ESP2UNIT_MANAUS") is True
    assert is_multi_company_dsn("WMS_VAREJO") is False
    assert is_multi_company_dsn("ESP2CORP") is False


def test_format_entity_name() -> None:
    assert format_entity_name("br-docto-wms") == "BrDoctoWms"
    assert format_entity_name("comprador") == "Comprador"


def test_build_pentaho_sql_multi_empresa() -> None:
    fields = [
        ("codigo", "character", 10, 0, "varchar"),
    ]
    sql = build_pentaho_table_input_sql(
        "comprador",
        fields,
        include_free_fields=True,
        empresa_code="35",
    )
    assert "'35' \"EMPRESA\"" in sql
    assert 'from pub."comprador"' in sql


def test_build_pentaho_sql_with_base() -> None:
    fields = [
        ("codigo", "character", 10, 0, "varchar"),
    ]
    sql = build_pentaho_table_input_sql(
        "cst-motivo",
        fields,
        include_free_fields=True,
        base_code="VAREJO",
    )
    assert "'VAREJO' \"BASE\"" in sql
    assert "[BASE]" not in sql
