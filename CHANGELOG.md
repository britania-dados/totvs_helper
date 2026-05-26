# Changelog

Todas as mudanças relevantes do projeto são registradas neste arquivo.  
**Desenvolvedores e agentes de IA:** durante o ciclo de trabalho (antes do próximo commit versionado), **atualize apenas este changelog** na seção da versão atual; **não** incremente `__version__` a cada solicitação. O **PATCH** sobe **uma vez** por lote entregável, **após** o commit que fechou a versão anterior (ver [CONVENTIONS.md](docs/ai/CONVENTIONS.md#versionamento)).

## 2.1.5

### Adicionado

- **Histórico persistente** (até 20 gerações) em `%APPDATA%\\TotvsHelper\\history.json` — restaura scripts após fechar o app.

### Alterado

- Toasts compactos no canto inferior direito; info neutro (sem vermelho de marca); clique para fechar; textos de feedback revisados.

### Corrigido

- Barra de status superior: erros e sucessos somem como o toast (✕ e auto-dismiss); mensagens de processamento não substituem o texto persistente.
- Exportação Pentaho com metadados da geração de scripts (inclui restauração do histórico): inferência a partir do DDL salvo e reconexão ODBC sob demanda quando necessário.
- Histórico: uma entrada por tabela (última data/hora); metadados de colunas persistidos para Pentaho.
- Toast após conectar DSN: `place()` não aceita `width`/`height` no CustomTkinter — largura no construtor do frame e empilhamento por altura real do widget.
- Pré-visualização de dados da tabela **emitente** (e outras muito largas): amostra ODBC omite colunas blob/binárias e limita a 64 colunas (PK primeiro), evitando falha no `SELECT TOP`.

### Documentação

- Seção **Idioma** em [CONVENTIONS.md](docs/ai/CONVENTIONS.md): projeto em português (UI, docs, changelog, **commits** e PRs); alinhamento em `AGENTS.md`, `docs/ai/README.md` e `.cursor/rules/totvs-helper-core.mdc`.

## 2.1.4

### Adicionado

- Remapeamento de chaves da tabela **emitente** na fonte **ECOM** nas cargas Pentaho (`cod-emitente` com offset `1000000000`; `nome-abrev` com prefixo `E_`), módulo compartilhado `ecom_emitente_keys.py` para reutilização no export SSIS (Fase 1).
- Switch/checkbox **ECOM** na tela de tabela e na tela de scripts (padrão desligado): altera apenas a **Query ETL** com remapeamento de chaves da tabela `emitente`.

### Documentação

- Regra de negócio em [`docs/ai/PENTAHO.md`](docs/ai/PENTAHO.md) e referência em [`docs/ai/PROJECT_CONTEXT.md`](docs/ai/PROJECT_CONTEXT.md); [`TODO.md`](TODO.md) Fase 1 SSIS aponta o módulo compartilhado.
- Política de versionamento: bump de PATCH **não** a cada tarefa do agente — apenas ao fechar um novo lote **depois** do commit da versão anterior ([CONVENTIONS.md](docs/ai/CONVENTIONS.md#versionamento)).

## 2.1.3

### Documentação

- Roadmap em [`TODO.md`](TODO.md): **Fase 1** exportação SSIS (`.dtsx`, incremental); **Fase 2** migração web Ubuntu + JDBC + HTMX (entrega única).
- Alinhamento de `AGENTS.md`, `docs/ai/PROJECT_CONTEXT.md`, `docs/ai/README.md`, `docs/ai/CONVENTIONS.md`, `README.md` e `.cursor/rules/totvs-helper-core.mdc` com o roadmap.
- Regra para agentes de IA: **cada entrega relevante deve incrementar a versão** automaticamente (`bump_version.py` + entrada neste changelog).

## 2.1.2

### Documentação

- Regra explícita: toda entrega com mudança de comportamento, build ou contrato deve atualizar **`CHANGELOG.md`** antes de concluir a tarefa.
- Orientação reforçada em `AGENTS.md`, `docs/ai/CONVENTIONS.md`, `docs/ai/README.md` e `.cursor/rules/totvs-helper-core.mdc`.

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
