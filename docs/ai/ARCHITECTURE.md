# Arquitetura — Totvs Helper

## Camadas

```text
main.py → app.main → TotvsHelperApp (ui/app_window.py)
                         ├── AppActions (ui/app_actions.py)  ← fluxos sem Tk
                         ├── shortcuts.py (atalhos de teclado)
                         ├── screens / widgets
                         └── SessionState (ui/state.py)
AppActions → OdbcClient (infra/) + ScriptGenerator + PentahoExporter (services/)
Settings + paths.py (config / caminhos dev e frozen)
errors.py → mensagens estáveis na UI (ConfigurationError, OdbcConnectionError)
```

## Fluxo do usuário

1. **DSN** — `OdbcClient.list_odbcs()` (ODBC da mesma arquitetura do `.exe`)
2. **Tabela** — metadados + preview via `OdbcClient`
3. **Scripts** — `ScriptGenerator.generate_helpers()`
4. Opcional: **Pentaho** — `services.pentaho.PentahoExporter`

A UI não contém regras SQL; só orquestra e exibe resultados.

## Onde alterar o quê

| Mudança | Onde |
|---------|------|
| SQL ETL / DDL / SSIS | `services/script_generator.py` + `tests/expected/` |
| Carga Pentaho | `services/pentaho/` + `packaging/pentaho/templates/` |
| ODBC / metadados | `infra/odbc_client.py` (`FieldMeta`) |
| Tela / navegação | `ui/app_window.py`, `ui/screens/` |
| Atalhos | `ui/shortcuts.py` |
| Credenciais | `.env` / `config/settings.py` |
| Build `.exe` | `scripts/build_exe.ps1`, `totvs_helper.spec` |

## ODBC (`infra/odbc_client.py`)

- Lista DSNs cujo driver contém `OpenEdge`.
- **64b vs 32b:** depende do executável (`TotvsHelper_64b.exe` / `_32b`), não do código.
- **`FieldMeta`:** metadados de coluna (`name`, `data_type`, `width`, `decimals`, `fetch_datatype`) retornados por `list_fields_and_pk`.
- **Listagem de tabelas (`list_tables`):** tenta, em ordem, consultas a `PUB._file`:
  1. `_Hidden = 0`
  2. `_Hidden = 0 OR NULL`
  3. `_tbl-type = 'T'`
  4. todas as linhas de `_file`
  5. fallback: catálogo ODBC (`cursor.tables`, schema `PUB` ou vazio)
- **Índices / PK:** lê `_prime-index` quando possível; várias queries de fallback em `list_table_indexes`.
- **Preview:** `SELECT TOP n` + fatia em Python (OpenEdge não suporta `SKIP` de forma confiável). Colunas blob/binárias são omitidas; no máximo 64 colunas (PK primeiro) — tabelas largas como `emitente`.
- **Conexão:** credenciais primárias, depois fallback do `.env`; falha → `OdbcConnectionError`.

## Erros (`errors.py`)

| Tipo | Quando | UI |
|------|--------|-----|
| `ConfigurationError` | `.env` ausente ou variável obrigatória | dialog na inicialização; banner em operações |
| `OdbcConnectionError` | DSN/credenciais/conexão | toast + banner via `user_message_for()` |

## Caminhos (`paths.py`)

Única fonte para `assets/`, templates Pentaho, `.env` (exe ao lado → bundle).

## Atalhos (`ui/shortcuts.py`)

| Atalho | Ação |
|--------|------|
| Enter | Confirmar / ação principal |
| Esc | Fechar overlay ou voltar |
| Ctrl+C | Copiar aba ativa |
| Ctrl+Shift+C | Copiar todas as abas |
| Ctrl+S | Salvar como… |
| F5 | Testar conexão DSN |
| Ctrl+, | Configurações |
| Ctrl+Tab / Ctrl+Shift+Tab | Abas na tela de resultados |

## Build

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1 -Python64 python
```

Com `-Python32`: também gera `TotvsHelper_32b.exe`. Python **instalador completo** com tkinter (não ZIP embeddable).
