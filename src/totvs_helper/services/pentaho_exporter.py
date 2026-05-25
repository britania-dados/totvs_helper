"""Generate Pentaho PDI 9.4 job and transformation from packaged templates."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from totvs_helper.services.pentaho_constants import (
    CONNECTION_PREFIX_BY_FAMILY,
    MULTI_BRANCHES,
    MULTI_TEMPLATE_BY_FAMILY,
    NON_MULTI_BASES,
    NON_MULTI_BASES_ESP2CORP,
    NON_MULTI_TEMPLATE_BY_FAMILY,
)
from totvs_helper.services.pentaho_constants import detect_source_family
from totvs_helper.services.pentaho_fields import (
    apply_field_metadata,
    escape_xml_text,
    filter_pentaho_fields,
)
from totvs_helper.services.pentaho_layout import (
    apply_job_gui_layout,
    normalize_job_transformation_entry,
)
from totvs_helper.services.pentaho_sql import (
    build_pentaho_table_input_sql,
    format_entity_name,
)
from totvs_helper.services.script_generator import ScriptGenerator

def _default_template_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "packaging" / "pentaho" / "templates"
    return Path(__file__).resolve().parents[3] / "packaging" / "pentaho" / "templates"

_TEMPLATE_PROGRESS_TABLE = {
    "BrDoctoWms": "br-docto-wms",
    "WmsItemEstabLocal": "wms-item-estab-local",
    "BrConferenciaRec": "Br-Conferencia-Rec",
}

_STEP_SQL_RE = re.compile(
    r"(<step>\s*<name>{step}</name>.*?<type>TableInput</type>.*?<sql>)(.*?)(</sql>)",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class PentahoExportResult:
    job_path: Path
    transformation_path: Path
    entity_name: str
    source_family: str


class PentahoExporter:
    """Clone sync templates and inject table-specific SQL and metadata."""

    def __init__(
        self,
        script_generator: Optional[ScriptGenerator] = None,
        *,
        template_root: Optional[Path] = None,
    ) -> None:
        self._generator = script_generator or ScriptGenerator()
        self._template_root = template_root or _default_template_root()

    def generate(
        self,
        output_dir: Path,
        *,
        progress_table: str,
        dsn: str,
        fields: List[Sequence],
        pk_fields: List[str],
        include_free_fields: bool,
        multi_company: bool,
    ) -> PentahoExportResult:
        entity = format_entity_name(progress_table)
        family = detect_source_family(dsn)

        if multi_company:
            if family not in MULTI_TEMPLATE_BY_FAMILY:
                raise ValueError(
                    f"DSN '{dsn}' ({family}) não suportado para carga multi. "
                    "Use esp2unit, ems2unit ou mov2unit."
                )
            template_key = MULTI_TEMPLATE_BY_FAMILY[family]
            template_entity = (
                "BrDoctoWms" if template_key == "multi_esp2unit" else "WmsItemEstabLocal"
            )
            conn_prefix = CONNECTION_PREFIX_BY_FAMILY[family]
            ktr_body = self._render_multi(
                template_key,
                template_entity,
                entity,
                progress_table,
                fields,
                pk_fields,
                include_free_fields,
                conn_prefix,
            )
        else:
            if family not in NON_MULTI_TEMPLATE_BY_FAMILY:
                raise ValueError(
                    f"DSN '{dsn}' ({family}) não suportado para carga não multi. "
                    "Use wms ou esp2corp."
                )
            template_key = NON_MULTI_TEMPLATE_BY_FAMILY[family]
            template_entity = "BrConferenciaRec"
            ktr_body = self._render_non_multi(
                template_key,
                template_entity,
                entity,
                progress_table,
                fields,
                pk_fields,
                include_free_fields,
                family,
            )

        kjb_body = self._render_job(template_key, template_entity, entity, progress_table)
        dataflows_dir = output_dir / "dataflows"
        dataflows_dir.mkdir(parents=True, exist_ok=True)

        ktr_path = dataflows_dir / f"dtf_{entity}.ktr"
        kjb_path = output_dir / f"wkf_{entity}.kjb"
        ktr_path.write_text(ktr_body, encoding="utf-8")
        kjb_path.write_text(kjb_body, encoding="utf-8")

        return PentahoExportResult(
            job_path=kjb_path,
            transformation_path=ktr_path,
            entity_name=entity,
            source_family=family,
        )

    def _template_dir(self, key: str) -> Path:
        path = self._template_root / key
        if not path.is_dir():
            raise FileNotFoundError(f"Template Pentaho não encontrado: {path}")
        return path

    def _read_template(self, key: str, filename: str) -> str:
        return (self._template_dir(key) / filename).read_text(encoding="utf-8")

    def _render_job(
        self, template_key: str, template_entity: str, entity: str, progress_table: str
    ) -> str:
        body = self._read_template(template_key, "wkf_TEMPLATE.kjb")
        body = _replace_entity(body, template_entity, entity, progress_table)
        body = normalize_job_transformation_entry(body, entity, template_entity)
        return apply_job_gui_layout(body, dtf_entry_name=f"dtf_{entity}")

    def _render_multi(
        self,
        template_key: str,
        template_entity: str,
        entity: str,
        progress_table: str,
        fields: List[Sequence],
        pk_fields: List[str],
        include_free_fields: bool,
        conn_prefix: str,
    ) -> str:
        body = self._read_template(template_key, "dataflows/dtf_TEMPLATE.ktr")
        body = _replace_entity(body, template_entity, entity, progress_table)
        body = _replace_connection_family(body, template_entity, conn_prefix)

        filtered = filter_pentaho_fields(fields, include_free_fields)
        source_steps = [name for name, _ in MULTI_BRANCHES]

        for step_name, empresa_code in MULTI_BRANCHES:
            sql = build_pentaho_table_input_sql(
                progress_table,
                filtered,
                include_free_fields=True,
                empresa_code=empresa_code,
            )
            body = _replace_step_sql(body, step_name, sql)

        return apply_field_metadata(
            body,
            filtered_fields=filtered,
            pk_fields=pk_fields,
            partition_field="EMPRESA",
            entity=entity,
            source_step_names=source_steps,
        )

    def _render_non_multi(
        self,
        template_key: str,
        template_entity: str,
        entity: str,
        progress_table: str,
        fields: List[Sequence],
        pk_fields: List[str],
        include_free_fields: bool,
        family: str,
    ) -> str:
        body = self._read_template(template_key, "dataflows/dtf_TEMPLATE.ktr")
        body = _replace_entity(body, template_entity, entity, progress_table)

        if family == "esp2corp":
            body = _fix_esp2corp_step_connections(body)
            branches = NON_MULTI_BASES_ESP2CORP
        else:
            branches = NON_MULTI_BASES

        filtered = filter_pentaho_fields(fields, include_free_fields)
        source_steps = [name for name, _, _ in branches]

        for step_name, _connection, base_code in branches:
            sql = build_pentaho_table_input_sql(
                progress_table,
                filtered,
                include_free_fields=True,
                base_code=base_code,
            )
            body = _replace_step_sql(body, step_name, sql)

        return apply_field_metadata(
            body,
            filtered_fields=filtered,
            pk_fields=pk_fields,
            partition_field="BASE",
            entity=entity,
            source_step_names=source_steps,
        )


def _replace_entity(
    text: str, template_entity: str, entity: str, progress_table: str
) -> str:
    template_slug = _TEMPLATE_PROGRESS_TABLE.get(
        template_entity, _entity_to_progress_slug(template_entity)
    )
    progress_slug = progress_table

    replacements = [
        (f"dtf_{template_entity}", f"dtf_{entity}"),
        (f"wkf_{template_entity}", f"wkf_{entity}"),
        (template_entity, entity),
        (f'pub."{template_slug}"', f'pub."{progress_slug}"'),
        (f'PUB."{template_slug}"', f'pub."{progress_slug}"'),
    ]
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def _entity_to_progress_slug(entity: str) -> str:
    """BrDoctoWms -> br-docto-wms (best effort)."""
    if entity.startswith("Br") and len(entity) > 2:
        core = entity[2:]
    elif entity.startswith("Wms") and len(entity) > 3:
        core = entity[3:]
    else:
        core = entity
    slug = re.sub(r"([a-z])([A-Z])", r"\1-\2", core).lower()
    return slug.replace("--", "-")


def _replace_connection_family(text: str, template_entity: str, new_prefix: str) -> str:
    if template_entity == "BrDoctoWms":
        old_prefix = "DATASUL_ESP2UNIT"
    else:
        old_prefix = "DATASUL_EMS2UNIT"
    if old_prefix == new_prefix:
        return text
    return text.replace(old_prefix, new_prefix)


def _replace_step_sql(body: str, step_name: str, sql: str) -> str:
    pattern = _STEP_SQL_RE.pattern.format(step=re.escape(step_name))
    regex = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    escaped = escape_xml_text(sql)

    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{escaped}{match.group(3)}"

    new_body, count = regex.subn(repl, body, count=1)
    if count == 0:
        raise ValueError(f"Passo TableInput '{step_name}' não encontrado no template.")
    return new_body


def _fix_esp2corp_step_connections(body: str) -> str:
    body = body.replace(
        "<connection>VAREJO</connection>", "<connection>DATASUL_ESP2CORP</connection>"
    )
    body = body.replace(
        "<connection>ECOM</connection>", "<connection>DATASUL_ESP2CORP_ECOM</connection>"
    )
    return body


