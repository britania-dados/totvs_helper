"""TXT serialization for generated helper scripts."""

from totvs_helper.services.script_generator import GeneratedScripts


def build_export_text(scripts: GeneratedScripts) -> str:
    """Create the text content exported by the UI."""
    sections = [
        ("Query para ETL", scripts.query_etl),
        ("Diferencial para divisao condicional do SSIS", scripts.differential),
        ("DDL de CREATE", scripts.ddl_create),
        ("Script para UPDATE", scripts.script_update),
        ("Script para DELETE", scripts.script_delete),
    ]

    separator = "*" * 150
    content_parts = []
    for index, (title, body) in enumerate(sections):
        content_parts.append(separator)
        content_parts.append(f"\n{title}:\n\n")
        content_parts.append(body)
        if index < len(sections) - 1:
            content_parts.append("\n\n\n\n")
    return "".join(content_parts)
