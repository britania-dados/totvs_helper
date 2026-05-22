from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.services.txt_exporter import build_export_text


def test_build_export_text_contains_all_sections():
    scripts = GeneratedScripts(
        query_etl="SELECT 1",
        ddl_create="CREATE TABLE X",
        script_delete="DELETE X",
        script_update="UPDATE X",
        differential="A != B",
    )

    exported = build_export_text(scripts)

    assert "Query para ETL:" in exported
    assert "Diferencial para divisao condicional do SSIS:" in exported
    assert "DDL de CREATE:" in exported
    assert "Script para UPDATE:" in exported
    assert "Script para DELETE:" in exported
