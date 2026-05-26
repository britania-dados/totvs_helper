# Changelog

## 2.1.1

### Adicionado

- Executáveis `TotvsHelper_64b.exe` e `TotvsHelper_32b.exe` (ODBC conforme arquitetura do `.exe`).
- Pacote `services/pentaho/` com shims de compatibilidade nos módulos `pentaho_*.py`.
- `ui/app_actions.py` — fluxos ODBC, scripts e Pentaho testáveis sem Tk.
- `paths.py` — caminhos dev/frozen (`.env`, assets, templates Pentaho).
- `FieldMeta` no `OdbcClient` — metadados de coluna tipados (`name`, `data_type`, etc.).
- `errors.py` — `ConfigurationError`, `OdbcConnectionError` e mensagens estáveis na UI.
- `filter_fields()` centralizado em `services/constants.py`.
- `ui/shortcuts.py` — atalhos de teclado documentados em `docs/ai/ARCHITECTURE.md`.
- `scripts/bump_version.py` — atualização de versão em `version.py` e `windows_version_info.txt`.
- `tests/test_app_actions.py`, `tests/test_errors.py`, `tests/conftest.py` (helper `field()`).
- `docs/ai/ARCHITECTURE.md` — camadas, fluxo, fallbacks ODBC, build.

### Alterado

- Build simplificado: `scripts/build_exe.ps1` com `-Python64` / `-Python32` (sem auto-detect `py -0p`).
- `totvs_helper.spec` lê versão de `version.py` inline; gera `windows_version_info.build.txt`.
- Estado UI unificado: removido `FlowStep`; `SessionState` como única fonte de DSN/tabela.
- `SessionState.release_connection()` no ciclo de vida ODBC.
- README, AGENTS e PROJECT_CONTEXT enxutos; índice aponta para ARCHITECTURE.

### Corrigido

- Troca de tema (claro ↔ escuro): UI não trava mais ao salvar Configurações; cores reaplicadas em todas as telas (`_refresh_theme`).

### Removido

- `scripts/generate_version_info.py` (versão inline no spec).
- Alias `GeneratedScripts.diferencial` — usar apenas `differential`.

## 2.1.0

- Geração de carga Pentaho PDI 9.4 na tela de scripts.

## 2.0.x

- UI CustomTkinter em etapas, histórico de sessão, exportação TXT.
