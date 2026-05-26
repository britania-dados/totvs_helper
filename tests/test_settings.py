import pytest

from totvs_helper import paths as paths_module
from totvs_helper.config import settings as settings_module
from totvs_helper.errors import ConfigurationError


def test_settings_load_raises_when_missing_required(monkeypatch):
    monkeypatch.setattr(settings_module, "_load_env_values", lambda _: None)
    monkeypatch.delenv("TOTVS_ODBC_USER_PRIMARY", raising=False)
    monkeypatch.delenv("TOTVS_ODBC_PASSWORD_PRIMARY", raising=False)
    monkeypatch.delenv("TOTVS_ODBC_USER_FALLBACK", raising=False)
    monkeypatch.delenv("TOTVS_ODBC_PASSWORD_FALLBACK", raising=False)

    with pytest.raises(ConfigurationError):
        settings_module.Settings.load()


def test_load_env_values_prefers_external_exe_env(tmp_path, monkeypatch):
    external_env = tmp_path / ".env"
    external_env.write_text(
        "TOTVS_ODBC_USER_PRIMARY=external_user\n",
        encoding="utf-8",
    )
    bundled_path = tmp_path / "bundle"
    bundled_path.mkdir()
    (bundled_path / ".env").write_text(
        "TOTVS_ODBC_USER_PRIMARY=bundled_user\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(paths_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        paths_module.sys, "executable", str(tmp_path / "app.exe"), raising=False
    )
    monkeypatch.setattr(
        paths_module.sys, "_MEIPASS", str(bundled_path), raising=False
    )
    monkeypatch.delenv("TOTVS_ODBC_USER_PRIMARY", raising=False)

    settings_module._load_env_values(".env")

    assert settings_module.os.getenv("TOTVS_ODBC_USER_PRIMARY") == "external_user"
