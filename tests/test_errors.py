from totvs_helper.errors import (
    ConfigurationError,
    OdbcConnectionError,
    user_message_for,
)


def test_user_message_for_domain_errors() -> None:
    assert user_message_for(ConfigurationError("Falta .env")) == "Falta .env"
    assert (
        user_message_for(OdbcConnectionError("DSN inválido")) == "DSN inválido"
    )


def test_user_message_for_generic_error() -> None:
    assert user_message_for(RuntimeError("falhou")) == "falhou"
