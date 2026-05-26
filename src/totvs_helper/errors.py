"""Domain errors with stable user-facing messages."""

from __future__ import annotations


class TotvsHelperError(Exception):
    """Base error for Totvs Helper."""

    user_message: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.user_message = message


class ConfigurationError(TotvsHelperError):
    """Missing or invalid application configuration."""


class OdbcConnectionError(TotvsHelperError):
    """ODBC connection or DSN failure."""


def user_message_for(exc: Exception) -> str:
    """Return a stable PT-BR message for UI toasts and banners."""
    if isinstance(exc, TotvsHelperError):
        return exc.user_message
    text = str(exc).strip()
    return text or "Erro inesperado. Consulte o log para detalhes."
