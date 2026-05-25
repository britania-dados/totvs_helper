"""Integration tests for Pentaho export."""

from __future__ import annotations

from pathlib import Path

import pytest

from totvs_helper.services.pentaho_exporter import PentahoExporter


@pytest.fixture
def sample_fields() -> list:
    return [
        ("cod-estabel", "character", 10, 0, "varchar"),
        ("cod-local", "character", 6, 0, "varchar"),
        ("num-docto", "character", 32, 0, "varchar"),
        ("id-docto", "integer", 0, 0, "integer"),
        ("dt-implant", "date", 0, 0, "datetime"),
        ("cod-usuario", "character", 24, 0, "varchar"),
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
