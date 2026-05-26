"""Tests for Pentaho job/KTR layout and naming."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from tests.conftest import field
from totvs_helper.services.pentaho_exporter import PentahoExporter
from totvs_helper.services.pentaho_layout import (
    _EMS2UNIT_GUI,
    apply_ktr_gui_layout,
    detect_layout_profile,
    normalize_job_transformation_entry,
)

# Referência: c:\temp\pdi2\dataflows\dtf_Item_depois.ktr
_ITEM_DEPOIS_GUI = dict(_EMS2UNIT_GUI)


def _gui_positions(ktr: str) -> dict[str, tuple[int, int]]:
    positions = {}
    for m in re.finditer(
        r"<step>\s*<name>([^<]+)</name>.*?<GUI>\s*<xloc>(\d+)</xloc>\s*<yloc>(\d+)</yloc>",
        ktr,
        re.DOTALL,
    ):
        positions[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return positions


def test_detect_ems2unit_profile() -> None:
    body = "<step><name>SV DATASUL</name><type>SelectValues</type></step>"
    assert detect_layout_profile(body) == "ems2unit"


def test_apply_layout_matches_item_depois() -> None:
    antes = Path(r"c:\temp\pdi2\dataflows\dtf_Item_antes.ktr")
    if not antes.is_file():
        pytest.skip("dtf_Item_antes.ktr não disponível")
    body = apply_ktr_gui_layout(
        antes.read_text(encoding="utf-8"),
        ["BRIC", "ECOM", "ELETRO", "NORDESTE", "PHILCO"],
        multi_company=True,
    )
    gui = _gui_positions(body)
    for step, expected in _ITEM_DEPOIS_GUI.items():
        if step in gui:
            assert gui[step] == expected, f"{step}: {gui[step]} != {expected}"

    assert gui["Sort rows"] != gui["SV STAGE"]
    assert gui["Select values"] != gui["Synchronize after merge"]


def test_normalize_job_transformation_entry_renames_generic() -> None:
    template = """
    <entries>
    <entry>
      <name>Transformation</name>
      <description/>
      <type>TRANS</type>
      <filename>dataflows/dtf_Old.ktr</filename>
      <transname/>
      <xloc>1</xloc>
      <yloc>2</yloc>
    </entry>
    </entries>
    <hops>
      <hop><from>Start</from><to>Transformation</to></hop>
      <hop><from>Transformation</from><to>Success</to></hop>
    </hops>
    """
    out = normalize_job_transformation_entry(template, "Item", "Old")
    assert "<name>dtf_Item</name>" in out
    assert "Transformation" not in out
    assert re.search(r"<transname>dtf_Item</transname>", out)
    assert "<to>dtf_Item</to>" in out


def test_generated_job_uses_dtf_entry_name() -> None:
    fields = [
        field("cod-estabel"),
        field("cod-local", width=6),
    ]
    exporter = PentahoExporter()
    with tempfile.TemporaryDirectory() as tmp:
        result = exporter.generate(
            Path(tmp),
            progress_table="item",
            dsn="EMS2UNIT_ELETRO",
            fields=fields,
            pk_fields=["cod-estabel"],
            include_free_fields=True,
            multi_company=True,
        )
        kjb = result.job_path.read_text(encoding="utf-8")
        ktr = result.transformation_path.read_text(encoding="utf-8")

    assert "<name>dtf_Item</name>" in kjb
    assert re.search(r"<transname>dtf_Item</transname>", kjb)
    assert "<to>Transformation</to>" not in kjb

    gui = _gui_positions(ktr)
    assert gui.get("SV DATASUL") == (672, 336)
    assert gui.get("Sort rows") == (432, 448)
    assert gui.get("SV STAGE") == (560, 448)
    assert gui.get("Synchronize after merge") == (1168, 448)
