"""Application orchestrator for Totvs Helper."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from totvs_helper.ui.splash_screen import StartupSplash

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    app_data = Path(os.getenv("APPDATA", Path.home()))
    log_dir = app_data / "TotvsHelper" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_dir / "totvs_helper.log",
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def run_with_splash(splash: "StartupSplash") -> int:
    """Load application modules and start UI; splash must already be visible."""
    try:
        splash.set_message("Carregando componentes...")
        import tkinter as tk

        from totvs_helper import __version__
        from totvs_helper.config.settings import Settings
        from totvs_helper.infra.odbc_client import OdbcClient
        from totvs_helper.services.script_generator import ScriptGenerator
        from totvs_helper.ui.app_window import TotvsHelperApp

        configure_logging()
        logger.info("Totvs Helper %s iniciado", __version__)

        splash.set_message("Lendo configurações...")
        settings = Settings.load()

        splash.set_message("Preparando serviços...")
        odbc_client = OdbcClient(settings)
        script_generator = ScriptGenerator()

        splash.set_message("Montando interface...")
        splash.pump()
        app = TotvsHelperApp(
            odbc_client=odbc_client,
            script_generator=script_generator,
        )
        # The splash owns the tkinter default root; transfer it to the app root
        # so CTkFont/Toast/etc. keep working after splash.close() (avoids
        # RuntimeError "Too early to use font: no default root window").
        tk._default_root = app.root
        splash.close()
        app.root.lift()
        app.root.focus_force()
        return app.run()
    except Exception as exc:
        logger.exception("Erro fatal na inicializacao")
        parent = getattr(locals().get("app"), "root", None)
        if parent is not None:
            try:
                import tkinter as tk

                tk._default_root = parent
            except Exception:
                pass
        try:
            splash.close()
        except Exception:
            pass
        try:
            from totvs_helper.ui.tk_dialogs import show_error

            show_error(
                "Totvs Helper",
                f"Ocorreu um erro durante a execução do Totvs Helper.\nDetalhes: {exc}",
                parent=parent,
            )
        except Exception:
            pass
        return 1


def run() -> int:
    from totvs_helper.ui.splash_screen import StartupSplash, close_pyinstaller_splash

    splash = StartupSplash()
    splash.show()
    close_pyinstaller_splash()
    return run_with_splash(splash)
