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
from totvs_helper.infra.odbc_client import OdbcClient
from totvs_helper.services.script_generator import GeneratedScripts, ScriptGenerator
from totvs_helper.services.txt_exporter import build_export_text
from totvs_helper.ui.preferences import (
    UserPreferences,
    load_preferences,
    save_preferences,
)
from totvs_helper.ui.screens import DsnScreen, HistoryPanel, ResultsScreen, TableScreen
from totvs_helper.ui.state import FlowStep, HistoryEntry, SessionState, SidebarView
from totvs_helper.ui.theme import (
    APP_TITLE,
    SIDEBAR_WIDTH,
    WINDOW_DEFAULT_SIZE,
    WINDOW_MIN_SIZE,
    apply_appearance,
    resolve_appearance,
    tokens,
)
from totvs_helper.ui.tk_dialogs import ask_ok_cancel, ask_save_filename, ask_yes_no
from totvs_helper.ui.widgets import (
    ErrorBanner,
    LoadingOverlay,
    SettingsDialog,
    Sidebar,
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


def _assets_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "assets"


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
        self._state = SessionState()
        self._prefs = load_preferences()
        self._busy = False
        self._selected_dsn: Optional[str] = None
        self._selected_table: Optional[str] = None
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

        self._toast = ToastManager(self.root, self._t)
        self._build_layout()
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

        main = ctk.CTkFrame(self.root, fg_color=self._t.bg)
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        self._error_banner = ErrorBanner(main, appearance_mode=self._appearance)
        self._error_banner.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._status_label = ctk.CTkLabel(
            main,
            text="Selecione um DSN OpenEdge.",
            font=ctk.CTkFont(size=12),
            text_color=self._t.text_muted,
            anchor="w",
        )
        self._status_label.grid(row=1, column=0, sticky="ew", pady=(0, 8))

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

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Return>", self._shortcut_enter)
        self.root.bind("<Escape>", self._shortcut_escape)
        self.root.bind("<Control-c>", self._shortcut_copy)
        self.root.bind("<Control-C>", self._shortcut_copy)
        self.root.bind("<Control-s>", self._shortcut_save)
        self.root.bind("<Control-S>", self._shortcut_save)
        self.root.bind("<Control-Shift-C>", self._shortcut_copy_all)
        self.root.bind("<Control-Shift-c>", self._shortcut_copy_all)
        self.root.bind("<F5>", self._shortcut_test)
        self.root.bind("<Control-comma>", self._shortcut_settings)
        self.root.bind_all("<Control-Tab>", self._shortcut_next_tab)
        self.root.bind_all("<Control-Shift-Tab>", self._shortcut_prev_tab)

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
            icon_path = _assets_dir() / "totvs_helper_logo.png"
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
            self._state.step = FlowStep.DSN
            self._dsn_screen.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(text="Conectar →")
        elif view == SidebarView.TABLE:
            self._state.step = FlowStep.TABLE
            self._table_screen.grid(row=0, column=0, sticky="nsew")
            self._btn_next.configure(text="Gerar scripts →")
        elif view == SidebarView.RESULTS:
            self._state.step = FlowStep.RESULTS
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
        self, message: str, *, error: bool = False, success: bool = False
    ) -> None:
        color = self._t.text_muted
        if error:
            color = self._t.danger
        elif success:
            color = self._t.success
        self._status_label.configure(text=message, text_color=color)

    def _show_error(self, message: str) -> None:
        self._set_status(message, error=True)
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
            self._set_status(message)

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
                        self._on_async_error(str(error))
                    elif on_success is not None:
                        on_success(result)  # type: ignore[arg-type]
                finally:
                    self._set_busy(False)

            self._run_on_ui_thread(on_done)

        threading.Thread(target=runner, daemon=True).start()

    def _on_async_error(self, message: str) -> None:
        self._show_error(message)
        self._toast.show(message, "error")

    def _load_dsn_list(self) -> None:
        self._dsn_list = self._odbc.list_odbcs()
        self._dsn_screen.set_items(self._dsn_list, selected=self._selected_dsn)
        if not self._dsn_list:
            self._show_error("Nenhum DSN OpenEdge encontrado.")

    def _apply_saved_dsn(self) -> None:
        if self._prefs.last_dsn and self._prefs.last_dsn in self._dsn_list:
            self._select_dsn(self._prefs.last_dsn)

    def _select_dsn(self, value: str) -> None:
        self._selected_dsn = value
        self._state.selected_odbc = value
        self._dsn_screen.select_value(value)
        self._set_status(f"DSN: {value}")

    def _select_table(self, value: str) -> None:
        if self._table_screen.preview.is_expanded:
            current = self._selected_table
            if current:
                self._table_screen.select_value(current)
            self._toast.show(
                "Recolha a pré-visualização para trocar de tabela.",
                "warning",
            )
            return
        self._selected_table = value
        self._state.selected_table = value
        self._table_screen.select_value(value)
        self._table_screen.preview.reset()
        self._set_status(f"Tabela: {value}")

    def _on_next(self) -> None:
        if self._state.view == SidebarView.DSN:
            if not self._selected_dsn:
                self._show_error("Selecione um DSN.")
                return
            self._connect_and_load_tables()
        elif self._state.view == SidebarView.TABLE:
            self._generate_scripts()

    def _on_back(self) -> None:
        if self._state.view == SidebarView.TABLE:
            self._close_connection()
            self._selected_table = None
            self._state.tables = []
            self._table_screen.preview.reset()
            self._show_view(SidebarView.DSN)
            self._set_status("Selecione um DSN.")
        elif self._state.view in (SidebarView.RESULTS, SidebarView.HISTORY):
            self._show_view(SidebarView.TABLE)

    def _test_connection(self) -> None:
        if not self._selected_dsn:
            self._show_error("Selecione um DSN.")
            return
        dsn = self._selected_dsn

        def on_success(_result: object) -> None:
            self._set_status(f"Conexão OK: {dsn}", success=True)
            self._toast.show(f"Conexão com {dsn} OK", "success")

        self._run_async(
            lambda: self._odbc.test_connection(dsn),
            busy_message=f"Testando {dsn}...",
            on_success=on_success,
        )

    def _connect_and_load_tables(self) -> None:
        dsn = self._selected_dsn
        if not dsn:
            return

        def work() -> Tuple[object, List[str]]:
            connection = self._odbc.connect(dsn)
            tables = self._odbc.list_tables(connection)
            return connection, tables

        def on_success(data: Tuple[object, List[str]]) -> None:
            connection, tables = data
            self._prefs.remember_dsn(dsn)
            save_preferences(self._prefs)
            self._state.connection = connection
            self._state.selected_odbc = dsn
            self._state.tables = tables
            self._selected_table = None
            self._table_screen.preview.reset()
            self._table_screen.set_items(tables)
            self._table_screen.set_dsn_context(dsn)
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
                    f"{len(tables)} tabelas em {dsn}",
                    "success",
                )
            self.root.update_idletasks()

        self._run_async(
            work,
            busy_message=f"Conectando {dsn}...",
            on_success=on_success,
        )

    def _load_table_preview(self, offset: int = 0) -> None:
        table = self._selected_table or self._table_screen.get_selected()
        connection = self._state.connection
        if not table or connection is None:
            self._show_error("Selecione uma tabela.")
            return

        if offset == 0:
            self._table_screen.preview.set_loading()
        else:
            self._table_screen.preview.set_sample_loading()

        def work() -> Dict[str, Any]:
            index_rows: list = []
            if offset == 0:
                recid = self._odbc.get_table_recid(table)
                fields, pk_fields = self._odbc.list_fields_and_pk(recid, connection)
                index_rows = self._odbc.list_table_indexes(
                    recid, connection, pk_fields
                )
            else:
                fields, pk_fields = self._table_screen.preview.get_field_cache()
                if not fields:
                    recid = self._odbc.get_table_recid(table)
                    fields, pk_fields = self._odbc.list_fields_and_pk(
                        recid, connection
                    )
            sample_columns: Optional[List[str]] = None
            sample_rows: Optional[list] = None
            sample_error: Optional[str] = None
            try:
                sample_columns, sample_rows = self._odbc.fetch_sample_rows(
                    table,
                    fields,
                    connection,
                    offset=offset,
                )
            except RuntimeError as exc:
                sample_error = str(exc)
            return {
                "fields": fields,
                "pk_fields": pk_fields,
                "index_rows": index_rows,
                "sample_columns": sample_columns,
                "sample_rows": sample_rows,
                "sample_error": sample_error,
            }

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

    def _generate_scripts(self) -> None:
        table = (
            self._selected_table or self._table_screen.get_selected() or ""
        ).strip()
        if table:
            self._selected_table = table
            self._table_screen.select_value(table)
        connection = self._state.connection
        if not table or connection is None:
            self._show_error("Selecione uma tabela na lista antes de gerar.")
            self._toast.show("Selecione uma tabela na lista.", "warning")
            return

        include_free = bool(self._table_screen.chk_free_fields.get())
        multi_company = bool(self._table_screen.chk_multi_company.get())
        self._state.include_free_fields = include_free
        self._state.multi_company = multi_company

        def work() -> GeneratedScripts:
            fields, pk_fields = self._table_screen.preview.get_field_cache()
            if not fields:
                recid = self._odbc.get_table_recid(table)
                fields, pk_fields = self._odbc.list_fields_and_pk(recid, connection)
            return self._generator.generate_helpers(
                include_free_fields=include_free,
                multi_company=multi_company,
                selected_table=table,
                fields=fields,
                pk_fields=pk_fields,
            )

        def on_success(scripts: GeneratedScripts) -> None:
            self._prefs.add_recent_table(table)
            save_preferences(self._prefs)
            self._state.scripts = scripts
            self._state.selected_table = table
            self._push_history(table, scripts)
            self._display_results(scripts, table)
            self._show_view(SidebarView.RESULTS)
            self._set_status("Scripts gerados.", success=True)
            self._toast.show("Scripts gerados com sucesso", "success")

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
        )
        self._state.history.add(entry)

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
        self._results_screen.set_context_chips(
            dsn, table, self._state.include_free_fields, self._state.multi_company
        )

    def _restore_history_entry(self, entry: HistoryEntry) -> None:
        self._state.scripts = entry.scripts
        self._state.selected_table = entry.table
        self._state.selected_odbc = entry.dsn
        self._state.include_free_fields = entry.include_free_fields
        self._state.multi_company = entry.multi_company
        self._display_results(entry.scripts, entry.table)
        self._show_view(SidebarView.RESULTS)
        self._toast.show(f"Restaurado: {entry.table}", "info")

    def _clear_history(self) -> None:
        self._state.history.clear()
        self._history_panel.set_entries([])
        self._toast.show("Histórico limpo", "info")

    def _copy_active_tab(self) -> None:
        text = self._results_screen.get_active_text()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            label = self._results_screen.get_active_label()
            self._toast.show(f"'{label}' copiado", "success")

    def _copy_all_tabs(self) -> None:
        scripts = self._state.scripts
        if scripts is None:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(build_export_text(scripts))
        self._toast.show("Todos os scripts copiados", "success")

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
            self._toast.show("Arquivo salvo", "success")
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
            self._close_connection()
            self._selected_dsn = None
            self._selected_table = None
            self._state.reset_for_new_process()
            self._dsn_screen.search_widget().delete(0, "end")
            self._table_screen.search_widget().delete(0, "end")
            self._table_screen.preview.reset()
            self._load_dsn_list()
            self._apply_saved_dsn()
            self._show_view(SidebarView.DSN)
            self._toast.show("Novo processo", "info")

    def _on_exit(self) -> None:
        if ask_ok_cancel(APP_TITLE, "Sair do Totvs Helper?", parent=self.root):
            self._close_connection()
            save_preferences(self._prefs)
            self.root.destroy()

    def _close_connection(self) -> None:
        if self._state.connection is not None:
            try:
                self._state.connection.close()
            except Exception:
                pass
            self._state.connection = None
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
            self._appearance = apply_appearance(resolved)
            self._t = tokens(self._appearance)
            self._sidebar.update_tokens(self._t)
            self._toast.update_tokens(self._t)
            self._dsn_screen.update_appearance(self._appearance)
            self._table_screen.update_appearance(self._appearance)
            self._results_screen.update_tokens(self._t)
            self._error_banner.update_mode(self._appearance)
            self.root.configure(fg_color=self._t.bg)
        self._toast.show("Configurações salvas", "success")

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
