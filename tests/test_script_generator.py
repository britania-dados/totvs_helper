from pathlib import Path

from tests.conftest import field
from totvs_helper.services.script_generator import ScriptGenerator


def test_generate_helpers_ignores_free_fields_when_disabled():
    generator = ScriptGenerator()
    fields = [
        field("char-1"),
        field("codigo", width=12),
        field("dt_cadastro", data_type="date", fetch_datatype="date"),
        field("ativo", data_type="logical", fetch_datatype="integer"),
    ]
    pk_fields = ["codigo"]

    scripts = generator.generate_helpers(
        include_free_fields=False,
        multi_company=True,
        selected_table="cad-cliente",
        fields=fields,
        pk_fields=pk_fields,
    )

    assert "char-1" not in scripts.query_etl
    assert "[empresa] [varchar](2)" in scripts.ddl_create
    assert "[codigo] = ?" in scripts.script_update
    assert "[empresa] = ?" in scripts.script_update
    assert "REPLACENULL([dt_cadastro]" in scripts.differential


def test_generate_helpers_includes_free_fields_when_enabled():
    generator = ScriptGenerator()
    fields = [
        field("char-1"),
        field("id", data_type="integer", fetch_datatype="integer"),
    ]
    pk_fields = ["id"]

    scripts = generator.generate_helpers(
        include_free_fields=True,
        multi_company=False,
        selected_table="cad-cli",
        fields=fields,
        pk_fields=pk_fields,
    )

    assert 'SUBSTRING("char-1",1,10)' in scripts.query_etl
    assert "[char-1] [varchar](10)" in scripts.ddl_create
    assert "[empresa]" not in scripts.ddl_create
    assert "[BASE] [varchar](8)" in scripts.ddl_create
    assert "    [BASE] " in scripts.ddl_create
    assert '"BASE"' in scripts.query_etl
    assert "[BASE] = ?" in scripts.script_update


def test_generate_helpers_maps_binary_type_to_varbinary_max():
    generator = ScriptGenerator()
    fields = [
        field("id", data_type="integer", fetch_datatype="integer"),
        field("arquivo", data_type="blob", fetch_datatype="blob"),
    ]
    pk_fields = ["id"]

    scripts = generator.generate_helpers(
        include_free_fields=True,
        multi_company=False,
        selected_table="anexos",
        fields=fields,
        pk_fields=pk_fields,
    )

    assert "[arquivo] [varbinary](max)" in scripts.ddl_create
    assert "FROM tot.[Anexos] A WITH(NOLOCK)" in scripts.script_delete


def test_generate_helpers_handles_multiple_pk_fields():
    generator = ScriptGenerator()
    fields = [
        field("filial", width=2),
        field("codigo", width=8),
        field("descricao", width=30),
    ]
    pk_fields = ["filial", "codigo"]

    scripts = generator.generate_helpers(
        include_free_fields=True,
        multi_company=False,
        selected_table="cad-prod",
        fields=fields,
        pk_fields=pk_fields,
    )

    assert "[filial] = ?" in scripts.script_update
    assert "[codigo] = ?" in scripts.script_update
    assert "[descricao] = ?" in scripts.script_update


def test_generate_helpers_matches_golden_files():
    generator = ScriptGenerator()
    fields = [
        field("id", data_type="integer", fetch_datatype="integer"),
        field("nome"),
    ]
    pk_fields = ["id"]

    scripts = generator.generate_helpers(
        include_free_fields=False,
        multi_company=True,
        selected_table="cad-cli",
        fields=fields,
        pk_fields=pk_fields,
    )

    expected_dir = Path(__file__).parent / "expected"
    assert scripts.query_etl == (expected_dir / "query_etl.sql").read_text(
        encoding="utf-8"
    ).rstrip("\n")
    assert scripts.ddl_create == (expected_dir / "ddl_create.sql").read_text(
        encoding="utf-8"
    ).rstrip("\n")
    assert scripts.script_update == (expected_dir / "script_update.sql").read_text(
        encoding="utf-8"
    ).rstrip("\n")
    assert scripts.script_delete == (expected_dir / "script_delete.sql").read_text(
        encoding="utf-8"
    ).rstrip("\n")
    assert scripts.differential == (expected_dir / "differential.txt").read_text(
        encoding="utf-8"
    ).rstrip("\n")
