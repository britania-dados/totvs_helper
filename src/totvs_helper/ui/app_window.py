"""Main application window with sidebar layout."""

from __future__ import annotations

import logging
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

import customtkinter as ctk

from totvs_helper import __version__
from totvs_helper.errors import TotvsHelperError, user_message_for
from totvs_helper.infra.odbc_client import OdbcClient
from totvs_helper.paths import assets_dir
from totvs_helper.services.metadata_from_scripts import infer_metadata_from_scripts
from totvs_helper.services.pentaho import PentahoExporter
from totvs_helper.services.script_generator import GeneratedScripts, ScriptGenerator
from totvs_helper.services.txt_exporter import build_export_text
from totvs_helper.ui.app_actions import AppActions
from totvs_helper.ui.history_store import load_history_entries, save_history_entries
from totvs_helper.ui.preferences import (
    UserPreferences,
    load_preferences,
    save_preferences,
)
from totvs_helper.ui.screens import DsnScreen, HistoryPanel, ResultsScreen, TableScreen
from totvs_helper.ui.shortcuts import bind_app_shortcuts
from totvs_helper.ui.state import HistoryEntry, SessionState, SidebarView
from totvs_helper.ui.theme import (
    APP_TITLE,
    SIDEBAR_WIDTH,
    WINDOW_DEFAULT_SIZE,
    WINDOW_MIN_SIZE,
    apply_appearance,
    resolve_appearance,
    tokens,
)
from totvs_helper.ui.tk_dialogs import (
    ask_directory,
    ask_ok_cancel,
    ask_save_filename,
    ask_yes_no,
)
from totvs_helper.ui.widgets import (
    ErrorBanner,
    LoadingOverlay,
    SettingsDialog,
    Sidebar,
    StatusBanner,
    ToastManager,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

TAB_KEYS = (
    "query_etl",
    "differential",
    "ddl_create",
    "script_update",
    "script_delete",
)


class TotvsHelperApp:
    """Sidebar-driven wizard for Totvs Helper."""

    def __init__(
        self,
        odbc_client: OdbcClient,
        script_generator: ScriptGenerator,
        *,
        root: Optional[ctk.CTk] = None,
    ) -> None:
        self._odbc = odbc_client
        self._generator = script_generator
        self._pentaho = PentahoExporter(script_generator)
        self._state = SessionState()
        self._actions = AppActions(
            odbc_client, script_generator, self._pentaho, self._state
        )
        self._prefs = load_preferences()
        self._busy = False
        self._dsn_list: List[str] = []

        resolved = resolve_appearance(self._prefs.appearance_mode)
        self._appearance = apply_appearance(resolved)
        self._t = tokens(self._appearance)

        self.root = root if root is not None else ctk.CTk()
        # Force this root to be the tkinter default; protects against late
        # font/widget creation after a sibling Tk (e.g., splash) is destroyed.
        tk._default_root = self.root
        self.root.title(f"{APP_TITLE} v{__version__}")
        self.root.geometry(f"{WINDOW_DEFAULT_SIZE[0]}x{WINDOW_DEFAULT_SIZE[1]}")
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(fg_color=self._t.bg)
        self._set_window_icon()
        self._bind_shortcuts()
        self._ui_queue: queue.Queue[Callable[[], None]] = queue.Queue()
        self._poll_ui_queue()

        self._build_layout()
        self._load_persisted_history()
        self._sync_sidebar_states()
        self._show_view(SidebarView.DSN)
        self._load_dsn_list()
        self._apply_saved_dsn()

    def run(self) -> int:
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        self.root.mainloop()
        save_preferences(self._prefs)
        return 0

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(
            self.root,
            self._t,
            on_navigate=self._on_sidebar_navigate,
            on_settings=self._open_settings,
            app_title=APP_TITLE,
            version=__version__,
            width=SIDEBAR_WIDTH,
        )
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._main = ctk.CTkFrame(self.root, fg_color=self._t.bg)
        self._main.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        main = self._main
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        self._error_banner = ErrorBanner(main, appearance_mode=self._appearance)
        self._error_banner.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._status_persistent = "Selecione um DSN OpenEdge."
        self._status_banner = StatusBanner(
            main,
            self._t,
            on_dismiss=self._restore_persistent_status,
        )
        self._status_banner.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._status_banner.show(
            self._status_persistent,
            color=self._t.text_muted,
            transient=False,
        )

        self._content = ctk.CTkFrame(main, fg_color="transparent")
        self._content.grid(row=2, column=0, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._loading = LoadingOverlay(self._content, fg_color=("gray90", "gray10"))

        self._dsn_screen = DsnScreen(
            self._content,
            self._t,
            self._appearance,
            on_test=self._test_connection,
            on_select=self._select_dsn,
            on_connect=self._connect_and_load_tables,
        )
        self._table_screen = TableScreen(
            self._content,
            self._t,
            self._appearance,
            on_select_table=self._select_table,
            on_generate=self._generate_scripts,
            on_preview=self._load_table_preview,
        )
        self._results_screen = ResultsScreen(
            self._content,
            self._t,
            on_copy_tab=self._copy_active_tab,
            on_copy_all=self._copy_all_tabs,
            on_save=self._save_txt,
            on_save_default=self._save_to_default_dir,
            on_script_options_changed=self._on_results_script_options_changed,
            on_generate_pentaho=self._generate_pentaho_load,
        )
        self._history_panel = HistoryPanel(
            self._content,
            self._t,
            on_restore=self._restore_history_entry,
            on_clear=self._clear_history,
        )

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(3, weight=1)

        self._btn_back = ctk.CTkButton(
            footer,
            text="← Voltar",
            width=110,
            fg_color="transparent",
            border_width=1,
            border_color=self._t.border,
            command=self._on_back,
        )
        self._btn_back.grid(row=0, column=0, padx=(0, 8))

        self._btn_restart = ctk.CTkButton(
            footer,
            text="Novo processo",
            width=130,
            fg_color="transparent",
            border_width=1,
            border_color=self._t.border,
            command=self._on_restart,
        )
        self._btn_restart.grid(row=0, column=1, padx=8)

        self._btn_exit = ctk.CTkButton(
            footer,
            text="Sair",
            width=90,
            fg_color=self._t.surface_alt,
            command=self._on_exit,
        )
        self._btn_exit.grid(row=0, column=2, padx=8)

        self._btn_next = ctk.CTkButton(
            footer,
            text="Continuar →",
            width=140,
            fg_color=self._t.accent,
            hover_color=self._t.accent_hover,
            command=self._on_next,
        )
        self._btn_next.grid(row=0, column=4, sticky="e")

        self._toast = ToastManager(
            self._main,
            self._t,
            anchor_left=self._btn_exit,
            anchor_right=self._btn_next,
        )

    def _bind_shortcuts(self) -> None:
        bind_app_shortcuts(
            self.root,
            {
                "<Return>": self._shortcut_enter,
                "<Escape>": self._shortcut_escape,
                "<Control-c>": self._shortcut_copy,
                "<Control-C>": self._shortcut_copy,
                "<Control-s>": self._shortcut_save,
                "<Control-S>": self._shortcut_save,
                "<Control-Shift-C>": self._shortcut_copy_all,
                "<Control-Shift-c>": self._shortcut_copy_all,
                "<F5>": self._shortcut_test,
                "<Control-comma>": self._shortcut_settings,
                "<Control-Tab>": self._shortcut_next_tab,
                "<Control-Shift-Tab>": self._shortcut_prev_tab,
            },
        )

    def _shortcut_next_tab(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.RESULTS:
            self._results_screen.cycle_tab(1)
            return "break"
        return None

    def _shortcut_prev_tab(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.RESULTS:
            self._results_screen.cycle_tab(-1)
            return "break"
        return None

    def _shortcut_enter(self, _event: tk.Event) -> Optional[str]:
        if self._is_text_focused() or self._busy:
            return None
        self._on_next()
        return "break"

    def _shortcut_escape(self, _event: tk.Event) -> str:
        if not self._busy and self._state.view != SidebarView.DSN:
            self._on_back()
        return "break"

    def _shortcut_copy(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.RESULTS:
            self._copy_active_tab()
            return "break"
        return None

    def _shortcut_copy_all(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.RESULTS:
            self._copy_all_tabs()
            return "break"
        return None

    def _shortcut_save(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.RESULTS:
            self._save_txt()
            return "break"
        return None

    def _shortcut_test(self, _event: tk.Event) -> Optional[str]:
        if self._state.view == SidebarView.DSN and not self._busy:
            self._test_connection()
            return "break"
        return None

    def _shortcut_settings(self, _event: tk.Event) -> str:
        self._open_settings()
        return "break"

    def _is_text_focused(self) -> bool:
        focused = self.root.focus_get()
        return isinstance(
            focused, (tk.Entry, tk.Text, tk.Listbox, ctk.CTkEntry, ctk.CTkTextbox)
        )

    def _set_window_icon(self) -> None:
        try:
            icon_path = assets_dir() / "totvs_helper_logo.png"
            if icon_path.exists():
                img = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, img)
                self._icon_image = img
        except Exception:
            logger.debug("Icone nao aplicado.", exc_info=True)

    def _on_sidebar_navigate(self, view: SidebarView) -> None:
        if view == SidebarView.HISTORY:
            self._show_view(SidebarView.HISTORY)
            return
        if view == SidebarView.TABLE and self._state.connection is None:
            self._toast.show("Conecte a um DSN primeiro.", "warning")
            return
        if view == SidebarView.RESULTS and self._state.scripts is None:
            self._toast.show("Gere os scripts antes de abrir esta etapa.", "warning")
            return
        self._show_view(view)

    def _show_view(self, view: SidebarView) -> None:
        self._state.view = view
        self._error_banner.hide()

        for screen in (
            self._dsn_screen,
            self._table_screen,
            self._results_screen,
            self._history_panel,
        ):
            screen.grid_forget()

        if view == SidebarView.DSN:
            self._dsn_screen.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(text="Conectar →")
        elif view == SidebarView.TABLE:
            self._table_screen.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(text="Gerar scripts →")
        elif view == SidebarView.RESULTS:
            self._results_screen.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(state="disabled")
        else:
            self._history_panel.set_entries(self._state.history.entries)
            self._history_panel.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(state="disabled")

        self._sidebar.set_active(view)
        self._sync_footer_buttons()
        self._sync_sidebar_states()

    def _sync_sidebar_states(self) -> None:
        connected = self._state.connection is not None
        has_scripts = self._state.scripts is not None

        self._sidebar.set_item_state(
            SidebarView.DSN, "active" if self._state.view == SidebarView.DSN else "done"
        )
        self._sidebar.set_item_state(
            SidebarView.TABLE,
            (
                "disabled"
                if not connected
                else ("active" if self._state.view == SidebarView.TABLE else "done")
            ),
        )
        self._sidebar.set_item_state(
            SidebarView.RESULTS,
            (
                "disabled"
                if not has_scripts
                else ("active" if self._state.view == SidebarView.RESULTS else "done")
            ),
        )
        self._sidebar.set_item_state(
            SidebarView.HISTORY,
            "active" if self._state.view == SidebarView.HISTORY else "idle",
        )
        self._sidebar.set_connected(connected, self._state.selected_odbc)

    def _sync_footer_buttons(self) -> None:
        view = self._state.view
        # The "next" button is meaningless on Results/History — hide it instead
        # of just disabling, so the footer doesn't carry a stale "Gerar scripts →".
        if view in (SidebarView.RESULTS, SidebarView.HISTORY):
            self._btn_next.grid_remove()
        else:
            self._btn_next.grid()

        if view == SidebarView.DSN:
            self._btn_back.configure(state="disabled")
            self._btn_restart.configure(state="disabled")
            self._btn_next.configure(state="normal" if not self._busy else "disabled")
        elif view == SidebarView.HISTORY:
            self._btn_back.configure(state="normal")
            self._btn_restart.configure(state="normal")
        elif view == SidebarView.RESULTS:
            self._btn_back.configure(state="normal")
            self._btn_restart.configure(state="normal")
        else:
            self._btn_back.configure(state="normal")
            self._btn_restart.configure(state="normal")
            self._btn_next.configure(state="normal" if not self._busy else "disabled")

    def _set_status(
        self,
        message: str,
        *,
        error: bool = False,
        success: bool = False,
        transient: bool | None = None,
        remember: bool = True,
    ) -> None:
        if transient is None:
            transient = bool(message) and (success or error)
        color = self._t.text_muted
        if error:
            color = self._t.danger
        elif success:
            color = self._t.success
        if remember and not transient:
            self._status_persistent = message
        self._status_banner.show(message, color=color, transient=transient)

    def _restore_persistent_status(self) -> None:
        if self._status_persistent:
            self._status_banner.show(
                self._status_persistent,
                color=self._t.text_muted,
                transient=False,
            )

    def _show_error(self, message: str) -> None:
        self._set_status(message, error=True, transient=True, remember=False)
        self._error_banner.show(message)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for w in (self._btn_back, self._btn_restart, self._btn_exit, self._btn_next):
            w.configure(state=state)
        if busy:
            self._loading.show(message or "Processando...")
        else:
            self._loading.hide()
            self._sync_footer_buttons()
        if message:
            self._set_status(message, remember=False)

    def _poll_ui_queue(self) -> None:
        """Drain UI callbacks queued from worker threads (Tk is not thread-safe)."""
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception:
                logger.exception("Erro ao processar callback da UI")
        self.root.after(50, self._poll_ui_queue)

    def _run_on_ui_thread(self, callback: Callable[[], None]) -> None:
        self._ui_queue.put(callback)

    def _run_async(
        self,
        work: Callable[[], T],
        *,
        busy_message: str,
        on_success: Optional[Callable[[T], None]] = None,
    ) -> None:
        if self._busy:
            self._toast.show("Aguarde a operação em andamento.", "warning")
            return
        self._set_busy(True, busy_message)

        def runner() -> None:
            error: Optional[Exception] = None
            result: Optional[T] = None
            try:
                result = work()
            except Exception as exc:
                error = exc
                logger.exception("Erro assincrono")

            def on_done() -> None:
                try:
                    if error is not None:
                        self._on_async_error(error)
                    elif on_success is not None:
                        on_success(result)  # type: ignore[arg-type]
                finally:
                    self._set_busy(False)

            self._run_on_ui_thread(on_done)

        threading.Thread(target=runner, daemon=True).start()

    def _on_async_error(self, error: Exception) -> None:
        message = user_message_for(error)
        self._show_error(message)
        self._toast.show(message, "error")

    def _load_dsn_list(self) -> None:
        self._dsn_list = self._actions.list_dsns()
        self._dsn_screen.set_items(self._dsn_list, selected=self._state.selected_odbc)
        if not self._dsn_list:
            self._show_error("Nenhum DSN OpenEdge encontrado.")

    def _apply_saved_dsn(self) -> None:
        if self._prefs.last_dsn and self._prefs.last_dsn in self._dsn_list:
            self._select_dsn(self._prefs.last_dsn)

    def _select_dsn(self, value: str) -> None:
        self._state.selected_odbc = value
        self._dsn_screen.select_value(value)
        self._actions.apply_dsn_option_defaults(value)
        self._set_status(f"DSN: {value}")

    def _select_table(self, value: str) -> None:
        if self._table_screen.preview.is_expanded:
            current = self._state.selected_table
            if current:
                self._table_screen.select_value(current)
            self._toast.show(
                "Recolha a pré-visualização para trocar de tabela.",
                "warning",
            )
            return
        self._state.selected_table = value
        self._table_screen.select_value(value)
        self._table_screen.preview.reset()
        self._set_status(f"Tabela: {value}")

    def _on_next(self) -> None:
        if self._state.view == SidebarView.DSN:
            if not self._state.selected_odbc:
                self._show_error("Selecione um DSN.")
                return
            self._connect_and_load_tables()
        elif self._state.view == SidebarView.TABLE:
            self._generate_scripts()

    def _on_back(self) -> None:
        if self._state.view == SidebarView.TABLE:
            self._close_connection()
            self._state.selected_table = None
            self._state.tables = []
            self._table_screen.preview.reset()
            self._show_view(SidebarView.DSN)
            self._set_status("Selecione um DSN.")
        elif self._state.view in (SidebarView.RESULTS, SidebarView.HISTORY):
            self._show_view(SidebarView.TABLE)

    def _test_connection(self) -> None:
        if not self._state.selected_odbc:
            self._show_error("Selecione um DSN.")
            return
        dsn = self._state.selected_odbc

        def on_success(_result: object) -> None:
            self._set_status(f"Conexão OK: {dsn}", success=True)
            self._toast.show(f"Conectado a {dsn}.", "success")

        self._run_async(
            lambda: self._actions.test_connection(dsn),
            busy_message=f"Testando {dsn}...",
            on_success=on_success,
        )

    def _connect_and_load_tables(self) -> None:
        dsn = self._state.selected_odbc
        if not dsn:
            return

        def work() -> Tuple[object, List[str]]:
            return self._actions.connect(dsn)

        def on_success(data: Tuple[object, List[str]]) -> None:
            connection, tables = data
            self._prefs.remember_dsn(dsn)
            save_preferences(self._prefs)
            self._state.connection = connection
            self._state.selected_odbc = dsn
            self._state.tables = tables
            self._state.selected_table = None
            self._table_screen.preview.reset()
            self._table_screen.set_items(tables)
            self._table_screen.set_dsn_context(dsn)
            self._actions.apply_dsn_option_defaults(dsn)
            self._table_screen.render_recent(
                [t for t in self._prefs.recent_tables if t in tables],
                on_pick=self._select_table,
            )
            self._show_view(SidebarView.TABLE)
            if not tables:
                message = (
                    f"Conectado em {dsn}, mas nenhuma tabela foi retornada. "
                    "Verifique permissões do usuário ODBC."
                )
                self._set_status(message, error=True)
                self._toast.show(message, "warning")
            else:
                self._set_status(
                    f"{len(tables)} tabelas carregadas em {dsn}.",
                    success=True,
                )
                self._toast.show(
                    f"{len(tables)} tabelas carregadas ({dsn}).",
                    "success",
                )
            self.root.update_idletasks()

        self._run_async(
            work,
            busy_message=f"Conectando {dsn}...",
            on_success=on_success,
        )

    def _load_table_preview(self, offset: int = 0) -> None:
        table = self._state.selected_table or self._table_screen.get_selected()
        connection = self._state.connection
        if not table or connection is None:
            self._show_error("Selecione uma tabela.")
            return

        if offset == 0:
            self._table_screen.preview.set_loading()
        else:
            self._table_screen.preview.set_sample_loading()

        def work() -> Dict[str, Any]:
            cached = self._table_screen.preview.get_field_cache() if offset else None
            return self._actions.load_table_preview(
                table,
                offset=offset,
                cached_fields=cached,
            )

        def on_success(data: Dict[str, Any]) -> None:
            self._table_screen.preview.set_data(
                table,
                list(data["fields"]),
                data["pk_fields"],
                index_rows=data["index_rows"],
                sample_columns=data["sample_columns"],
                sample_rows=data["sample_rows"],
                sample_error=data["sample_error"],
                sample_offset=offset,
                reload_metadata=offset == 0,
            )

        page = offset // 10 + 1
        self._run_async(
            work,
            busy_message=f"Carregando {table} (página {page})...",
            on_success=on_success,
        )

    def _sync_table_option_checkboxes(self) -> None:
        self._table_screen.apply_option_defaults(
            include_free_fields=self._state.include_free_fields,
            multi_company=self._state.multi_company,
            ecom_keys=self._state.ecom_keys,
        )

    def _apply_script_options(
        self, include_free_fields: bool, multi_company: bool, ecom_keys: bool
    ) -> None:
        self._state.include_free_fields = include_free_fields
        self._state.multi_company = multi_company
        self._state.ecom_keys = ecom_keys
        self._sync_table_option_checkboxes()

    def _on_results_script_options_changed(self) -> None:
        include_free, multi_company, ecom_keys = self._results_screen.get_script_options()
        if (
            include_free == self._state.include_free_fields
            and multi_company == self._state.multi_company
            and ecom_keys == self._state.ecom_keys
        ):
            return
        self._apply_script_options(include_free, multi_company, ecom_keys)
        self._regenerate_scripts(
            push_history=False,
            navigate_to_results=False,
            success_toast=False,
        )

    def _generate_scripts(self) -> None:
        table = (
            self._state.selected_table or self._table_screen.get_selected() or ""
        ).strip()
        if table:
            self._state.selected_table = table
            self._table_screen.select_value(table)
        connection = self._state.connection
        if not table or connection is None:
            self._show_error("Selecione uma tabela na lista antes de gerar.")
            self._toast.show("Selecione uma tabela na lista.", "warning")
            return

        include_free = bool(self._table_screen.chk_free_fields.get())
        multi_company = bool(self._table_screen.chk_multi_company.get())
        ecom_keys = bool(self._table_screen.chk_ecom_keys.get())
        self._apply_script_options(include_free, multi_company, ecom_keys)
        self._regenerate_scripts(
            table=table,
            push_history=True,
            navigate_to_results=True,
            success_toast=True,
        )

    def _regenerate_scripts(
        self,
        *,
        table: Optional[str] = None,
        push_history: bool,
        navigate_to_results: bool,
        success_toast: bool,
    ) -> None:
        table = (table or self._state.selected_table or "").strip()
        connection = self._state.connection
        if not table or connection is None:
            return

        def work() -> tuple[GeneratedScripts, list, list]:
            fields, pk_fields = self._table_screen.preview.get_field_cache()
            if not fields:
                fields, pk_fields = self._actions.resolve_fields_for_table(table, [])
            scripts = self._actions.generate_scripts(table, fields, pk_fields)
            return scripts, list(fields), list(pk_fields)

        def on_success(payload: tuple[GeneratedScripts, list, list]) -> None:
            scripts, fields, pk_fields = payload
            self._state.table_fields = fields
            self._state.table_pk_fields = pk_fields
            if push_history:
                self._prefs.add_recent_table(table)
                save_preferences(self._prefs)
            self._state.scripts = scripts
            self._state.selected_table = table
            if push_history:
                self._push_history(table, scripts)
            self._display_results(scripts, table)
            if navigate_to_results:
                self._show_view(SidebarView.RESULTS)
            self._set_status("Scripts gerados.", success=True)
            if success_toast:
                self._toast.show("Scripts gerados.", "success")
            elif push_history is False:
                self._toast.show("Scripts recalculados.", "info")

        self._run_async(
            work,
            busy_message=f"Gerando {table}...",
            on_success=on_success,
        )

    def _push_history(self, table: str, scripts: GeneratedScripts) -> None:
        dsn = self._state.selected_odbc or ""
        entry = HistoryEntry(
            dsn=dsn,
            table=table,
            include_free_fields=self._state.include_free_fields,
            multi_company=self._state.multi_company,
            scripts=scripts,
            ecom_keys=self._state.ecom_keys,
            table_fields=list(self._state.table_fields),
            table_pk_fields=list(self._state.table_pk_fields),
        )
        self._state.history.add(entry)
        self._persist_history()

    def _load_persisted_history(self) -> None:
        self._state.history.entries = load_history_entries()
        self._history_panel.set_entries(self._state.history.entries)
        self._persist_history()

    def _persist_history(self) -> None:
        save_history_entries(self._state.history.entries)

    def _display_results(self, scripts: GeneratedScripts, table: str) -> None:
        mapping = {
            "query_etl": scripts.query_etl,
            "differential": scripts.differential,
            "ddl_create": scripts.ddl_create,
            "script_update": scripts.script_update,
            "script_delete": scripts.script_delete,
        }
        self._results_screen.set_scripts(mapping)
        dsn = self._state.selected_odbc or ""
        self._results_screen.set_context(
            dsn,
            table,
            include_free_fields=self._state.include_free_fields,
            multi_company=self._state.multi_company,
            ecom_keys=self._state.ecom_keys,
        )

    def _restore_history_entry(self, entry: HistoryEntry) -> None:
        self._state.scripts = entry.scripts
        self._state.selected_table = entry.table
        self._state.selected_odbc = entry.dsn
        fields, pk_fields = self._metadata_for_history_entry(entry)
        self._state.table_fields = fields
        self._state.table_pk_fields = pk_fields
        if fields and not entry.table_fields:
            self._upsert_history_metadata(entry, fields, pk_fields)
        self._status_persistent = f"DSN: {entry.dsn}"
        self._set_status(f"Tabela: {entry.table}")
        self._apply_script_options(
            entry.include_free_fields,
            entry.multi_company,
            entry.ecom_keys,
        )
        self._display_results(entry.scripts, entry.table)
        self._show_view(SidebarView.RESULTS)
        self._toast.show(
            f"Scripts de {entry.table} restaurados do histórico.",
            "success",
        )

    def _clear_history(self) -> None:
        self._state.history.clear()
        self._history_panel.set_entries([])
        self._persist_history()
        self._toast.show("Histórico apagado.", "success")

    def _get_table_metadata_for_export(self) -> tuple[list, list]:
        """Fields/PK from script generation, then preview cache."""
        if self._state.table_fields:
            return list(self._state.table_fields), list(self._state.table_pk_fields)
        preview_fields, preview_pk = self._table_screen.preview.get_field_cache()
        if preview_fields:
            return list(preview_fields), list(preview_pk)
        return [], []

    def _metadata_for_history_entry(
        self, entry: HistoryEntry
    ) -> tuple[list, list]:
        if entry.table_fields:
            return list(entry.table_fields), list(entry.table_pk_fields)
        return infer_metadata_from_scripts(entry.scripts)

    def _upsert_history_metadata(
        self, entry: HistoryEntry, fields: list, pk_fields: list
    ) -> None:
        updated = HistoryEntry(
            dsn=entry.dsn,
            table=entry.table,
            include_free_fields=entry.include_free_fields,
            multi_company=entry.multi_company,
            scripts=entry.scripts,
            ecom_keys=entry.ecom_keys,
            table_fields=list(fields),
            table_pk_fields=list(pk_fields),
            created_at=entry.created_at,
        )
        key = entry.history_key
        self._state.history.entries = [
            updated if e.history_key == key else e for e in self._state.history.entries
        ]
        self._persist_history()

    def _resolve_pentaho_metadata(
        self, table: str, dsn: str, *, allow_odbc: bool
    ) -> tuple[list, list]:
        fields, pk_fields = self._get_table_metadata_for_export()
        if fields:
            return fields, pk_fields

        scripts = self._state.scripts
        if scripts:
            fields, pk_fields = infer_metadata_from_scripts(scripts)
            if fields:
                self._state.table_fields = list(fields)
                self._state.table_pk_fields = list(pk_fields)
                same_ctx = (
                    self._state.selected_table == table
                    and self._state.selected_odbc == dsn
                )
                if same_ctx:
                    hist_key = (dsn.casefold(), table.casefold())
                    for entry in self._state.history.entries:
                        if entry.history_key == hist_key:
                            self._upsert_history_metadata(entry, fields, pk_fields)
                            break
                return fields, pk_fields

        if allow_odbc and dsn:
            connection = self._state.connection
            close_after = False
            if connection is None:
                connection, _ = self._actions.connect(dsn)
                close_after = True
            try:
                fields, pk_fields = self._actions.resolve_fields_for_table(table, [])
            finally:
                if close_after:
                    try:
                        connection.close()
                    except Exception:
                        pass
            if fields:
                self._state.table_fields = list(fields)
                self._state.table_pk_fields = list(pk_fields)
                return fields, pk_fields

        return [], []

    def _generate_pentaho_load(self) -> None:
        table = (self._state.selected_table or "").strip()
        dsn = self._state.selected_odbc or ""
        if not table or not dsn:
            self._toast.show(
                "Gere os scripts antes de exportar a carga Pentaho.", "warning"
            )
            return

        initial_dir = self._prefs.export_directory()
        output_dir = ask_directory(
            parent=self.root,
            title="Pasta para gerar wkf/dtf Pentaho",
            initialdir=initial_dir,
        )
        if not output_dir:
            return

        if self._state.scripts is None:
            self._toast.show(
                "Gere ou restaure os scripts antes de exportar a carga Pentaho.",
                "warning",
            )
            return

        def work() -> Path:
            fields, pk_fields = self._resolve_pentaho_metadata(
                table, dsn, allow_odbc=True
            )
            if not fields:
                raise TotvsHelperError(
                    "Metadados da tabela indisponíveis para Pentaho."
                )
            return self._actions.generate_pentaho(
                Path(output_dir),
                table,
                dsn,
                fields,
                pk_fields,
            )

        def on_success(job_path: Path) -> None:
            self._prefs.last_export_dir = str(job_path.parent.parent)
            save_preferences(self._prefs)
            self._set_status(f"Carga Pentaho: {job_path}", success=True)
            self._toast.show("Carga Pentaho gerada.", "success")

        self._run_async(
            work,
            busy_message=f"Gerando carga Pentaho {table}...",
            on_success=on_success,
        )

    def _copy_active_tab(self) -> None:
        text = self._results_screen.get_active_text()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            label = self._results_screen.get_active_label()
            self._toast.show(f"{label} copiado.", "success")

    def _copy_all_tabs(self) -> None:
        scripts = self._state.scripts
        if scripts is None:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(build_export_text(scripts))
        self._toast.show("Todos os scripts copiados.", "success")

    def _save_txt(self) -> None:
        scripts = self._state.scripts
        if scripts is None:
            self._show_error("Nada para exportar.")
            return
        initial_dir = self._prefs.export_directory()
        default_name = f"{(self._state.selected_table or 'totvs').lower()}_helpers.txt"
        filename = ask_save_filename(
            parent=self.root,
            title="Salvar helpers",
            defaultextension=".txt",
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
        )
        if filename:
            self._write_export(Path(filename))

    def _save_to_default_dir(self) -> None:
        scripts = self._state.scripts
        if scripts is None:
            self._show_error("Nada para exportar.")
            return
        export_dir = Path(self._prefs.export_directory())
        export_dir.mkdir(parents=True, exist_ok=True)
        name = f"{(self._state.selected_table or 'totvs').lower()}_helpers.txt"
        self._write_export(export_dir / name)

    def _write_export(self, path: Path) -> None:
        scripts = self._state.scripts
        if scripts is None:
            return
        try:
            path.write_text(build_export_text(scripts), encoding="utf-8")
            self._prefs.last_export_dir = str(path.parent)
            save_preferences(self._prefs)
            self._set_status(f"Salvo: {path}", success=True)
            self._toast.show("Arquivo salvo.", "success")
            if self._prefs.ask_open_folder and ask_yes_no(
                APP_TITLE,
                "Abrir pasta do arquivo?",
                parent=self.root,
            ):
                self._open_folder(path.parent)
        except OSError as exc:
            self._show_error(str(exc))

    def _on_restart(self) -> None:
        if self._state.view == SidebarView.DSN and not self._state.connection:
            return
        if ask_yes_no(APP_TITLE, "Iniciar novo processo?", parent=self.root):
            self._state.reset_for_new_process()
            self._sidebar.set_connected(False)
            self._dsn_screen.search_widget().delete(0, "end")
            self._table_screen.search_widget().delete(0, "end")
            self._table_screen.preview.reset()
            self._load_dsn_list()
            self._apply_saved_dsn()
            self._show_view(SidebarView.DSN)
            self._toast.show("Novo processo iniciado.", "success")

    def _on_exit(self) -> None:
        if ask_ok_cancel(APP_TITLE, "Sair do Totvs Helper?", parent=self.root):
            self._close_connection()
            save_preferences(self._prefs)
            self.root.destroy()

    def _close_connection(self) -> None:
        self._state.release_connection()
        self._sidebar.set_connected(False)

    def _open_settings(self) -> None:
        SettingsDialog(
            self.root,
            self._t,
            self._prefs,
            on_save=self._apply_settings,
        )

    def _apply_settings(self, prefs: UserPreferences) -> None:
        self._prefs = prefs
        save_preferences(prefs)
        resolved = resolve_appearance(prefs.appearance_mode)
        if resolved != self._appearance:
            apply_appearance(resolved)
            self.root.after(0, lambda: self._refresh_theme(resolved))
        self._toast.show("Configurações salvas.", "success")

    def _refresh_theme(self, appearance: str) -> None:
        """Re-apply design tokens to widgets with explicit colors."""
        self._appearance = appearance
        self._t = tokens(appearance)
        t = self._t

        self.root.configure(fg_color=t.bg)
        self._main.configure(fg_color=t.bg)
        self._loading.configure(fg_color=t.bg)

        self._sidebar.update_tokens(t)
        self._toast.update_tokens(t)
        self._status_banner.update_tokens(t)
        self._error_banner.update_mode(appearance)
        self._dsn_screen.update_tokens(t, appearance)
        self._table_screen.update_tokens(t, appearance)
        self._results_screen.update_tokens(t)
        self._history_panel.update_tokens(t)

        self._btn_back.configure(
            border_color=t.border,
            hover_color=t.surface_alt,
            text_color=t.text,
        )
        self._btn_restart.configure(
            border_color=t.border,
            hover_color=t.surface_alt,
            text_color=t.text,
        )
        self._btn_exit.configure(fg_color=t.surface_alt, text_color=t.text)
        self._btn_next.configure(
            fg_color=t.accent,
            hover_color=t.accent_hover,
            text_color="#ffffff",
        )

        self._sync_sidebar_states()
        self._sync_footer_buttons()
        self.root.update_idletasks()

    @staticmethod
    def _open_folder(directory: Path) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(str(directory))  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", str(directory)], check=False)
            else:
                subprocess.run(["xdg-open", str(directory)], check=False)
        except OSError as exc:
            logger.warning("Pasta: %s", exc)
