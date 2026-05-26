"""Tests for Pentaho field metadata rebuild."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tests.conftest import field
from totvs_helper.services.pentaho_fields import (
    apply_field_metadata,
    build_stage_select_sql,
    discover_sort_step_names,
    filter_pentaho_fields,
    stage_column_names,
    sync_value_field_names,
)


def test_filter_and_stage_sql() -> None:
    fields = [
        field("cod-estabel"),
        field("cod-local", width=6),
        field("id-docto", data_type="integer", fetch_datatype="integer"),
        field("cod-livre-1", width=100),
    ]
    filtered = filter_pentaho_fields(fields, include_free_fields=False)
    assert len(filtered) == 3
    cols = stage_column_names(filtered, "EMPRESA")
    sql = build_stage_select_sql("BrTeste", cols)
    assert "[cod-estabel]" in sql
    assert "[id-docto]" in sql
    assert "[EMPRESA]" in sql
    assert "[CHKSUM]" in sql
    assert "cod-livre-1" not in sql


def test_discover_sort_step_names_from_hops() -> None:
    body = """
    <order>
      <hop><from>STAGE</from><to>Sort stage</to></hop>
      <hop><from>Add a checksum</from><to>Sort TOTVS</to></hop>
    </order>
    """
    assert discover_sort_step_names(body) == ("Sort stage", "Sort TOTVS")


def test_apply_field_metadata_on_minimal_ktr_fragment() -> None:
    template = """<transformation>
  <step>
    <name>Add a checksum</name>
    <type>CheckSum</type>
    <fields>
      <field><name>old</name></field>
    </fields>
  </step>
  <step>
    <name>Sort stage</name>
    <type>SortRows</type>
    <fields>
      <field><name>old</name></field>
    </fields>
  </step>
  <step>
    <name>SORT TOTVS</name>
    <type>SortRows</type>
    <fields>
      <field><name>old</name></field>
    </fields>
  </step>
  <order>
    <hop><from>STAGE</from><to>Sort stage</to></hop>
    <hop><from>Add a checksum</from><to>SORT TOTVS</to></hop>
  </order>
  <step>
    <name>STAGE</name>
    <type>TableInput</type>
    <sql>SELECT [old] FROM [tot].[Tpl]</sql>
    <row-meta><value-meta><name>old</name></value-meta></row-meta>
  </step>
  <step>
    <name>BRIC</name>
    <type>TableInput</type>
    <sql>select 1</sql>
    <row-meta><value-meta><name>old</name></value-meta></row-meta>
  </step>
  <step>
    <name>Merge rows (diff)</name>
    <type>MergeRows</type>
    <keys><key>old</key></keys>
  </step>
  <step>
    <name>Synchronize after merge</name>
    <type>SynchronizeAfterMerge</type>
    <lookup>
      <schema>tot</schema>
      <table>Tpl</table>
      <key><name>old</name><field>old</field><condition>=</condition><name2/></key>
      <value><name>old</name><rename>old</rename><update>N</update></value>
    </lookup>
  </step>
</transformation>"""
    fields = [
        field("cod-estabel"),
        field("cod-local", width=6),
        field("id-docto", data_type="integer", fetch_datatype="integer"),
    ]
    filtered = filter_pentaho_fields(fields, True)
    out = apply_field_metadata(
        template,
        filtered_fields=filtered,
        pk_fields=["cod-estabel", "cod-local"],
        partition_field="EMPRESA",
        entity="BrTeste",
        source_step_names=["BRIC"],
    )
    assert "<name>cod-estabel</name>" in out
    assert "<name>cod-local</name>" in out
    assert "<name>id-docto</name>" in out
    assert "<name>EMPRESA</name>" in out
    assert "<name>CHKSUM</name>" in out
    assert "<name>DataCarga</name>" in out
    assert "old" not in out
    assert len(sync_value_field_names(filtered, "EMPRESA")) == 6
    ET.fromstring(out)


def test_apply_field_metadata_produces_valid_xml() -> None:
    """row-meta replacement must not nest duplicate tags."""
    import tempfile
    from pathlib import Path

    from totvs_helper.services.pentaho_exporter import PentahoExporter

    exporter = PentahoExporter()
    fields = [
        field("cod-estabel"),
        field("cod-local", width=6),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = exporter.generate(
            Path(tmp),
            progress_table="br-conferencia-rec",
            dsn="WMS_VAREJO",
            fields=fields,
            pk_fields=["cod-estabel", "cod-local"],
            include_free_fields=True,
            multi_company=False,
        )
        ktr = result.transformation_path.read_text(encoding="utf-8")
    assert "<row-meta>\n    <row-meta>" not in ktr
    assert ktr.count("<step>") == ktr.count("</step>")
    ET.fromstring(ktr)
