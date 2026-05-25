"""Rebuild Pentaho step field metadata from ODBC table columns."""

from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from totvs_helper.services.constants import FREE_FIELDS_TO_IGNORE

# (pentaho_type, length, precision, conversion_mask)
_PentahoMeta = Tuple[str, int, int, str]

_ROW_META_COMMON = """        <storagetype>normal</storagetype>
        <name>{name}</name>
        <length>{length}</length>
        <precision>{precision}</precision>
        <origin>{origin}</origin>
        <comments>{name}</comments>
        <conversion_Mask>{mask}</conversion_Mask>
        <decimal_symbol>{decimal}</decimal_symbol>
        <grouping_symbol>{grouping}</grouping_symbol>
        <currency_symbol/>
        <trim_type>none</trim_type>
        <case_insensitive>N</case_insensitive>
        <collator_disabled>Y</collator_disabled>
        <collator_strength>0</collator_strength>
        <sort_descending>N</sort_descending>
        <output_padding>N</output_padding>
        <date_format_lenient>N</date_format_lenient>
        <date_format_locale>pt_BR</date_format_locale>
        <date_format_timezone>America/Sao_Paulo</date_format_timezone>
        <lenient_string_to_number>N</lenient_string_to_number>"""


def filter_pentaho_fields(
    fields: List[Sequence], include_free_fields: bool
) -> List[Sequence]:
    return [
        field
        for field in fields
        if include_free_fields or field[0] not in FREE_FIELDS_TO_IGNORE
    ]


def stream_field_names(
    filtered_fields: List[Sequence], partition_field: str
) -> List[str]:
    return [field[0] for field in filtered_fields] + [partition_field]


def stage_column_names(
    filtered_fields: List[Sequence], partition_field: str
) -> List[str]:
    return stream_field_names(filtered_fields, partition_field) + ["CHKSUM"]


def sort_field_names(pk_fields: List[str], partition_field: str) -> List[str]:
    names = list(pk_fields)
    if partition_field not in names:
        names.append(partition_field)
    return names


def sync_value_field_names(
    filtered_fields: List[Sequence],
    partition_field: str,
    *,
    load_date_field: str = "DataCarga",
) -> List[str]:
    return stream_field_names(filtered_fields, partition_field) + [
        "CHKSUM",
        load_date_field,
    ]


def build_stage_select_sql(entity: str, column_names: List[str]) -> str:
    if not column_names:
        raise ValueError("STAGE precisa de ao menos uma coluna.")
    first = f"SELECT [{column_names[0]}]"
    rest = "".join(f"\n      ,[{name}]" for name in column_names[1:])
    return f"{first}{rest}\nFROM [tot].[{entity}]"


def discover_sort_step_names(body: str) -> Tuple[str, str]:
    """Resolve SortRows step names from hops (STAGE / Add a checksum)."""
    stage_hop = re.search(
        r"<from>\s*STAGE\s*</from>\s*<to>\s*([^<]+?)\s*</to>",
        body,
        re.IGNORECASE,
    )
    totvs_hop = re.search(
        r"<from>\s*Add a checksum\s*</from>\s*<to>\s*([^<]+?)\s*</to>",
        body,
        re.IGNORECASE,
    )
    if stage_hop and totvs_hop:
        return stage_hop.group(1).strip(), totvs_hop.group(1).strip()

    sort_steps = re.findall(
        r"<step>\s*<name>([^<]+)</name>\s*<type>SortRows</type>",
        body,
        re.IGNORECASE,
    )
    if len(sort_steps) >= 2:
        return sort_steps[0].strip(), sort_steps[1].strip()

    raise ValueError(
        "Passos SortRows não encontrados no template "
        "(esperado hop STAGE→Sort e Add a checksum→Sort)."
    )


def discover_load_date_field(body: str) -> str:
    """SystemInfo step field used as DataCarga in sync."""
    match = re.search(
        r"<step>\s*<name>[^<]+</name>\s*<type>SystemInfo</type>.*?<fields>\s*"
        r"<field>\s*<name>([^<]+)</name>",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else "DataCarga"


def apply_field_metadata(
    body: str,
    *,
    filtered_fields: List[Sequence],
    pk_fields: List[str],
    partition_field: str,
    entity: str,
    source_step_names: List[str],
) -> str:
    """Replace template column lists with all table columns."""
    stream_names = stream_field_names(filtered_fields, partition_field)
    stage_names = stage_column_names(filtered_fields, partition_field)
    checksum_names = stream_names
    sort_names = sort_field_names(pk_fields, partition_field)
    sync_keys = sort_names
    load_date = discover_load_date_field(body)
    sync_values = sync_value_field_names(
        filtered_fields, partition_field, load_date_field=load_date
    )
    sort_stage, sort_totvs = discover_sort_step_names(body)

    body = _replace_checksum_fields(body, checksum_names)
    body = _replace_sort_fields(body, sort_stage, sort_names)
    body = _replace_sort_fields(body, sort_totvs, sort_names)
    body = _replace_stage_table_input(body, entity, stage_names, filtered_fields, partition_field)
    for step_name in source_step_names:
        body = _replace_table_input_row_meta(
            body, step_name, filtered_fields, partition_field, origin=step_name
        )
    body = _replace_sync_keys(body, sync_keys, sync_values)

    from totvs_helper.services.pentaho_layout import apply_ktr_gui_layout

    return apply_ktr_gui_layout(
        body,
        source_step_names,
        multi_company=partition_field == "EMPRESA",
    )


def _pentaho_meta(
    field: Sequence | str, *, partition: bool = False
) -> _PentahoMeta:
    if partition:
        name = str(field)
        return "String", 8 if name == "BASE" else 2, -1, ""
    data_type = field[1]
    width = int(field[2] or 0)
    decimals = int(field[3] or 0)
    if data_type == "character":
        return "String", width, -1, ""
    if data_type == "date":
        return "Date", -1, -1, ""
    if data_type == "logical":
        return "Boolean", -1, -1, ""
    if data_type == "integer":
        return "BigNumber", 17, 2, (
            "######0.0###################;-######0.0###################"
        )
    if data_type in ("decimal", "numeric"):
        return "BigNumber", max(width, 17), decimals, (
            "######0.0###################;-######0.0###################"
        )
    return "String", width or 255, -1, ""


def _build_value_meta(
    name: str,
    meta: _PentahoMeta,
    *,
    origin: str,
    stage: bool,
) -> str:
    ptype, length, precision, mask = meta
    decimal = "." if stage and ptype == "BigNumber" else ","
    grouping = "" if stage and ptype == "BigNumber" else "."
    return (
        "      <value-meta>\n"
        f"        <type>{ptype}</type>\n"
        + _ROW_META_COMMON.format(
            name=name,
            length=length,
            precision=precision,
            mask=mask,
            decimal=decimal,
            grouping=grouping,
            origin=origin,
        )
        + "\n      </value-meta>\n"
    )


def _build_row_meta(
    filtered_fields: List[Sequence],
    partition_field: str,
    *,
    origin: str,
    stage: bool,
) -> str:
    parts = [
        _build_value_meta(
            field[0], _pentaho_meta(field), origin=origin, stage=stage
        )
        for field in filtered_fields
    ]
    parts.append(
        _build_value_meta(
            partition_field,
            _pentaho_meta(partition_field, partition=True),
            origin=origin,
            stage=stage,
        )
    )
    if stage:
        parts.append(
            _build_value_meta(
                "CHKSUM",
                ("String", 40, -1, ""),
                origin=origin,
                stage=True,
            )
        )
    return "<row-meta>\n" + "".join(parts) + "    </row-meta>"


def _replace_checksum_fields(body: str, field_names: List[str]) -> str:
    inner = "".join(
        f"      <field>\n        <name>{name}</name>\n      </field>\n"
        for name in field_names
    )
    pattern = (
        r"(<step>\s*<name>[^<]+</name>\s*<type>CheckSum</type>.*?<fields>)"
        r"(.*?)(</fields>)"
    )
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Passo CheckSum não encontrado no template.")
    return body[: match.start(2)] + "\n" + inner + body[match.end(2) :]


def _replace_sort_fields(body: str, step_name: str, field_names: List[str]) -> str:
    inner = "".join(
        "      <field>\n"
        f"        <name>{name}</name>\n"
        "        <ascending>Y</ascending>\n"
        "        <case_sensitive>N</case_sensitive>\n"
        "        <collator_enabled>N</collator_enabled>\n"
        "        <collator_strength>0</collator_strength>\n"
        "        <presorted>N</presorted>\n"
        "      </field>\n"
        for name in field_names
    )
    pattern = (
        rf"(<step>\s*<name>{re.escape(step_name)}</name>.*?<type>SortRows</type>.*?<fields>)"
        r"(.*?)(</fields>)"
    )
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"Passo SortRows '{step_name}' não encontrado no template.")
    return body[: match.start(2)] + "\n" + inner + body[match.end(2) :]


def _replace_stage_table_input(
    body: str,
    entity: str,
    column_names: List[str],
    filtered_fields: List[Sequence],
    partition_field: str,
) -> str:
    sql = escape_xml_text(build_stage_select_sql(entity, column_names))
    row_meta = _build_row_meta(
        filtered_fields, partition_field, origin="STAGE", stage=True
    )
    pattern = (
        r"(<step>\s*<name>STAGE</name>.*?<type>TableInput</type>.*?<sql>)"
        r"(.*?)(</sql>)"
        r"(.*?)(<row-meta>)(.*?)(</row-meta>)"
    )
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Passo STAGE não encontrado no template.")
    return (
        body[: match.start(2)]
        + sql
        + match.group(3)
        + match.group(4)
        + row_meta
        + body[match.end(7) :]
    )


def _replace_table_input_row_meta(
    body: str,
    step_name: str,
    filtered_fields: List[Sequence],
    partition_field: str,
    *,
    origin: str,
) -> str:
    row_meta = _build_row_meta(
        filtered_fields, partition_field, origin=origin, stage=False
    )
    pattern = (
        rf"(<step>\s*<name>{re.escape(step_name)}</name>.*?<type>TableInput</type>.*?)"
        r"(<row-meta>)(.*?)(</row-meta>)"
    )
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"row-meta do passo '{step_name}' não encontrado.")
    return body[: match.start(2)] + row_meta + body[match.end(4) :]


def _replace_sync_keys(
    body: str, key_fields: List[str], value_field_names: List[str]
) -> str:
    body = _replace_mergerows_keys(body, key_fields)
    body = _replace_synchronize_lookup(body, key_fields, value_field_names)
    return body


def _replace_mergerows_keys(body: str, key_fields: List[str]) -> str:
    keys_xml = "".join(f"      <key>{name}</key>\n" for name in key_fields)
    pattern = (
        r"(<step>.*?<type>MergeRows</type>.*?<keys>)(.*?)(</keys>)"
    )
    match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not match:
        return body
    return body[: match.start(2)] + "\n" + keys_xml + body[match.end(2) :]


def _replace_synchronize_lookup(
    body: str, key_fields: List[str], value_field_names: List[str]
) -> str:
    step_re = re.compile(
        r"(<step>.*?<type>SynchronizeAfterMerge</type>.*?)(</step>)",
        re.DOTALL | re.IGNORECASE,
    )
    match = step_re.search(body)
    if not match:
        return body

    step_xml = match.group(1)
    lookup_match = re.search(r"<lookup>(.*?)</lookup>", step_xml, re.DOTALL)
    if not lookup_match:
        return body

    lookup_inner = lookup_match.group(1)
    schema_match = re.search(r"<schema>([^<]*)</schema>", lookup_inner)
    table_match = re.search(r"<table>([^<]*)</table>", lookup_inner)
    schema = schema_match.group(1) if schema_match else "tot"
    table = table_match.group(1) if table_match else ""

    keys_block = "".join(
        "      <key>\n"
        f"        <name>{name}</name>\n"
        f"        <field>{name}</field>\n"
        "        <condition>=</condition>\n"
        "        <name2/>\n"
        "      </key>\n"
        for name in key_fields
    )
    key_set = set(key_fields)
    values_block = ""
    for name in value_field_names:
        update_flag = "N" if name in key_set else "Y"
        values_block += (
            "      <value>\n"
            f"        <name>{name}</name>\n"
            f"        <rename>{name}</rename>\n"
            f"        <update>{update_flag}</update>\n"
            "      </value>\n"
        )

    new_lookup = (
        f"\n      <schema>{schema}</schema>\n"
        f"      <table>{table}</table>\n"
        f"{keys_block}"
        f"{values_block}"
    )
    step_xml = step_xml.replace(
        lookup_match.group(0), f"<lookup>{new_lookup}    </lookup>"
    )
    return body.replace(match.group(0), step_xml + match.group(2))


def escape_xml_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
