"""Application settings loaded from environment variables."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the application."""

    odbc_user_primary: str
    odbc_password_primary: str
    odbc_user_fallback: str
    odbc_password_fallback: str
    odbc_timeout_seconds: int = 30

    @classmethod
    def load(cls, env_file: str = ".env") -> "Settings":
        """Load settings from environment with smart .env fallback."""
        _load_env_values(env_file)

        timeout = int(os.getenv("TOTVS_ODBC_TIMEOUT", "30"))
        if timeout < 5:
            logger.warning(
                "TOTVS_ODBC_TIMEOUT=%s é baixo; conexões grandes (ex.: EMS2UNIT) "
                "podem falhar. Recomendado: 30.",
                timeout,
            )

        return cls(
            odbc_user_primary=_get_required_env("TOTVS_ODBC_USER_PRIMARY"),
            odbc_password_primary=_get_required_env("TOTVS_ODBC_PASSWORD_PRIMARY"),
            odbc_user_fallback=_get_required_env("TOTVS_ODBC_USER_FALLBACK"),
            odbc_password_fallback=_get_required_env("TOTVS_ODBC_PASSWORD_FALLBACK"),
            odbc_timeout_seconds=timeout,
        )


def _get_required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value:
        return value

    raise ValueError(
        f"Variavel de ambiente obrigatoria ausente: {var_name}. "
        "Crie um arquivo .env baseado em .env.example."
    )


def _load_env_values(env_file: str) -> None:
    """Load environment variables from external or bundled .env file."""
    env_paths = []

    if getattr(sys, "frozen", False):
        # Priority 1: external .env beside the executable, if present.
        exe_dir = Path(sys.executable).resolve().parent
        env_paths.append(exe_dir / env_file)

        # Priority 2: .env bundled inside the executable by PyInstaller.
        bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        env_paths.append(bundle_dir / env_file)
    else:
        project_root = Path(__file__).resolve().parents[3]
        env_paths.append(project_root / env_file)

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            logger.info("Variaveis carregadas de %s", env_path)
            return

    logger.warning(
        "Nenhum arquivo %s encontrado. Usando variaveis de ambiente do sistema.",
        env_file,
    )
