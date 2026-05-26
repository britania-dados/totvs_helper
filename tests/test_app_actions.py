from unittest.mock import Mock

from tests.conftest import field
from totvs_helper.services.script_generator import GeneratedScripts
from totvs_helper.ui.app_actions import AppActions
from totvs_helper.ui.state import SessionState


def test_generate_scripts_uses_state_flags():
    odbc = Mock()
    generator = Mock()
    generator.generate_helpers.return_value = GeneratedScripts(
        query_etl="q",
        ddl_create="d",
        script_delete="del",
        script_update="u",
        differential="diff",
    )
    pentaho = Mock()
    state = SessionState()
    state.include_free_fields = False
    state.multi_company = True

    actions = AppActions(odbc, generator, pentaho, state)
    fields = [field("codigo", width=12)]
    actions.generate_scripts("my-table", fields, ["codigo"])

    generator.generate_helpers.assert_called_once()
    kwargs = generator.generate_helpers.call_args.kwargs
    assert kwargs["include_free_fields"] is False
    assert kwargs["multi_company"] is True
    assert kwargs["ecom_keys"] is False
    assert kwargs["selected_table"] == "my-table"


def test_generate_scripts_passes_ecom_keys_flag():
    odbc = Mock()
    generator = Mock()
    generator.generate_helpers.return_value = GeneratedScripts(
        query_etl="q",
        ddl_create="d",
        script_delete="del",
        script_update="u",
        differential="diff",
    )
    pentaho = Mock()
    state = SessionState()
    state.ecom_keys = True

    actions = AppActions(odbc, generator, pentaho, state)
    actions.generate_scripts("emitente", [field("cod-emitente")], ["cod-emitente"])

    assert generator.generate_helpers.call_args.kwargs["ecom_keys"] is True
