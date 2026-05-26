"""Integration tests for Pentaho export."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import field
from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.services.pentaho_exporter import PentahoExporter


@pytest.fixture
def sample_fields() -> list[FieldMeta]:
    return [
        field("cod-estabel"),
        field("cod-local", width=6),
        field("num-docto", width=32),
        field("id-docto", data_type="integer", fetch_datatype="integer"),
        field("dt-implant", data_type="date", fetch_datatype="datetime"),
        field("cod-usuario", width=24),
    ]


def test_generate_multi_esp2unit(tmp_path: Path, sample_fields: list) -> None:
    exporter = PentahoExporter()
    result = exporter.generate(
        tmp_path,
        progress_table="br-docto-wms",
        dsn="ESP2UNIT_ELETRO",
        fields=sample_fields,
        pk_fields=["cod-estabel", "cod-local", "id-docto"],
        include_free_fields=True,
        multi_company=True,
    )
    assert result.job_path.exists()
    assert result.transformation_path.exists()
    ktr = result.transformation_path.read_text(encoding="utf-8")
    assert "dtf_BrDoctoWms" in result.job_path.read_text(encoding="utf-8")
    assert "BrDoctoWms" in ktr
    assert 'pub."br-docto-wms"' in ktr
    assert "DATASUL_ESP2UNIT_BRIC" in ktr
    assert "'35' \"EMPRESA\"" in ktr
    assert "SynchronizeAfterMerge" in ktr
    for col in ("num-docto", "dt-implant", "cod-usuario"):
        assert f"<name>{col}</name>" in ktr
    assert ktr.count("<name>cod-estabel</name>") >= 4
    assert "[num-docto]" in ktr
    assert "[dt-implant]" in ktr


def test_generate_non_multi_wms(tmp_path: Path, sample_fields: list) -> None:
    exporter = PentahoExporter()
    result = exporter.generate(
        tmp_path,
        progress_table="br-conferencia-rec",
        dsn="WMS_VAREJO",
        fields=sample_fields,
        pk_fields=["cod-estabel", "cod-local"],
        include_free_fields=True,
        multi_company=False,
    )
    ktr = result.transformation_path.read_text(encoding="utf-8")
    assert "'VAREJO' \"BASE\"" in ktr
    assert "'ECOM' \"BASE\"" in ktr
    assert "<key>BASE</key>" in ktr or "<name>BASE</name>" in ktr
    assert "[cod-usuario]" in ktr
    assert ktr.count("<name>cod-estabel</name>") >= 4


def test_generate_multi_ems2unit_sort_rows(tmp_path: Path, sample_fields: list) -> None:
    """ems2unit template uses Sort rows / Sort rows 2 instead of SORT STAGE."""
    exporter = PentahoExporter()
    result = exporter.generate(
        tmp_path,
        progress_table="wms-item-estab-local",
        dsn="EMS2UNIT_ELETRO",
        fields=sample_fields,
        pk_fields=["cod-estabel", "cod-local"],
        include_free_fields=True,
        multi_company=True,
    )
    ktr = result.transformation_path.read_text(encoding="utf-8")
    assert "<name>num-docto</name>" in ktr
    assert "Sort rows" in ktr
