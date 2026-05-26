# Guia para agentes de IA (Cursor, Claude Code, etc.)

Este arquivo é o ponto de entrada para assistentes de código trabalharem no **Totvs Helper**. Leia-o antes de alterar o repositório.

Documentação complementar:

| Documento | Conteúdo |
|-----------|----------|
| [README.md](README.md) | Instalação, build, uso humano, troubleshooting |
| [docs/ai/ARCHITECTURE.md](docs/ai/ARCHITECTURE.md) | Camadas, fluxo, onde alterar código |
| [docs/ai/PROJECT_CONTEXT.md](docs/ai/PROJECT_CONTEXT.md) | Domínio, fluxos, módulos |
| [docs/ai/CONVENTIONS.md](docs/ai/CONVENTIONS.md) | Padrões de código, testes, git, changelog, o que evitar |
| [docs/ai/PENTAHO.md](docs/ai/PENTAHO.md) | Geração de cargas PDI 9.4 (`.kjb` / `.ktr`) |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões — **obrigatório atualizar** em entregas com mudança visível |
| [TODO.md](TODO.md) | Roadmap — **Fase 1:** exportação SSIS; **Fase 2:** web (entrega única) |

Regras Cursor (aplicadas automaticamente no IDE): `.cursor/rules/*.mdc`

---

## O que é o projeto

**Totvs Helper** é um app desktop Windows (Python 3.9) que conecta em bancos **TOTVS / OpenEdge** via ODBC, lê metadados de tabelas e gera artefatos ETL:

- Scripts SQL (query ETL, DDL, UPDATE, DELETE, expressão diferencial SSIS na aba de resultados)
- Exportação Pentaho PDI 9.4 (`wkf_*.kjb` + `dataflows/dtf_*.ktr`)
- **Em desenvolvimento (Fase 1):** exportação de pacote SSIS (`.dtsx`) — ver [TODO.md](TODO.md)

**Não** executa ETL, **não** conecta em SQL Server de produção para carga — apenas gera arquivos.

**Cliente / contexto:** Britânia Eletrodomésticos. Projeto **em português**: UI, documentação, changelog, **mensagens de commit** e descrições de PR (ver [CONVENTIONS.md — Idioma](docs/ai/CONVENTIONS.md#idioma)). Código: identificadores em inglês onde o módulo já segue inglês.

**Versão atual:** `src/totvs_helper/version.py` (`__version__`, hoje `2.1.5`).

**Versionamento:** em toda entrega relevante, atualizar **`CHANGELOG.md`** na seção da versão atual. **Bump** (`python scripts/bump_version.py X.Y.Z`) **apenas uma vez por lote**, depois do commit que fechou a versão anterior — **não** a cada solicitação do agente. Detalhes: [CONVENTIONS.md — Versionamento](docs/ai/CONVENTIONS.md#versionamento).

---

## Stack e restrições

| Camada | Tecnologia |
|--------|------------|
| UI | CustomTkinter + Tkinter, Pygments |
| DB | pyodbc → OpenEdge (Progress) |
| Empacotamento | PyInstaller (`totvs_helper.spec`) |
| Qualidade | ruff, black, pytest, mypy |

Restrições importantes:

- **Windows** como alvo principal (ODBC, `.exe`, paths `%APPDATA%`).
- **Python 3.9** — não usar sintaxe 3.10+ sem necessidade.
- **Credenciais:** `.env` nunca commitar; build embute `.env` em `TotvsHelper_64b.exe` / `TotvsHelper_32b.exe` (ver README).
- **Mudanças mínimas** — preferir diff focado; não refatorar fora do escopo.
- **Commits / push** só quando o usuário pedir explicitamente.

---

## Estrutura do repositório (mapa mental)

```text
totvs_helper/
  main.py                 # Entry: delega para totvs_helper.app.main.run
  src/totvs_helper/
    app/main.py           # Logging, splash, wiring ODBC + UI
    paths.py              # assets, templates, .env (dev/frozen)
    config/settings.py    # .env / variáveis ODBC
    infra/odbc_client.py  # DSN, tabelas, campos, PK, índices, amostra TOP 10
    services/
      script_generator.py   # SQL helpers (core)
      pentaho/            # Export PDI (templates XML)
      constants.py        # filter_fields, campos livres
    ui/
      app_window.py       # Layout, navegação, async
      app_actions.py      # Fluxos ODBC/scripts/Pentaho (sem Tk)
      state.py            # SessionState
      screens/            # dsn, table, results, history
      widgets/            # componentes reutilizáveis
    version.py
  packaging/pentaho/templates/  # Templates .kjb/.ktr (bundled no .exe)
  tests/                  # pytest; expected/ para golden files SQL
  assets/                 # ícone, splash
  scripts/                # build_exe.ps1, generate_icon.py
```

**Fluxo UI (3 etapas):** DSN → Tabela/opções → Scripts (+ Pentaho; + SSIS na Fase 1). Estado em `SessionState`; operações ODBC em thread + `queue` para não travar UI.

---

## Roadmap (fonte: [TODO.md](TODO.md))

| Fase | Objetivo | Como implementar |
|------|----------|------------------|
| **1** | **Exportação** SSIS (`.dtsx`) no desktop | **Incremental** — etapas 1–5 no TODO (template → `services/ssis/` → botão na UI → homologação) |
| **2** | App **web** (Ubuntu + JDBC + HTMX) | **Entrega única** — um PR com todo o checklist da Fase 2; substitui desktop |

**Já existe:** scripts SQL + aba **Diferencial SSIS** (`ScriptGenerator.differential`). **Fase 1 não** recria isso — adiciona **exportar o pacote `.dtsx`**, espelhando Pentaho.

**Ao codificar:**

- Trabalho em **Fase 1:** seguir a etapa atual do TODO; diff mínimo; manter desktop e ODBC.
- Pedido de **Fase 2:** implementar o **checklist completo** da Fase 2 de uma vez (não entregar só “spike JDBC” ou só API); pré-requisito = Fase 1 concluída.
- Deploy/homologação no Ubuntu = validação humana pós-merge (`[humano]` no TODO).

---

## Comandos úteis para o agente

```powershell
# Ambiente
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# Desenvolvimento
$env:PYTHONPATH = "src"
python main.py

# Qualidade (rodar antes de considerar PR pronto)
ruff check .
black --check .
pytest
mypy src

# Build exe (lento; só se pedido)
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1 -Python64 python -Python32 "...\python32.exe"
```

---

## Onde implementar funcionalidades comuns

| Pedido do usuário | Onde olhar / editar |
|-------------------|---------------------|
| Novo script SQL / regra ETL | `services/script_generator.py`, `tests/test_script_generator.py`, `tests/expected/` |
| Metadados / SQL OpenEdge | `infra/odbc_client.py`, testes `test_odbc_*.py` |
| Tela / botão / layout | `ui/screens/*`, `ui/app_window.py`, `ui/widgets/*` |
| Export Pentaho | `services/pentaho/`, `packaging/pentaho/templates/`, [PENTAHO.md](docs/ai/PENTAHO.md) |
| Export SSIS (Fase 1) | `services/ssis/` (criar), `packaging/ssis/templates/`, `AppActions.generate_ssis()`, `ResultsScreen` — ver [TODO.md](TODO.md) |
| Versão / build desktop | `version.py`, `packaging/windows_version_info.txt`, `totvs_helper.spec` |
| Migração web (Fase 2) | `web/`, `jdbc_client.py`, `application/` — checklist único em [TODO.md](TODO.md); remove `ui/` na mesma entrega |

---

## Armadilhas conhecidas (leia antes de debugar)

1. **`RuntimeError: Too early to use font`** — Tk precisa de `tk._default_root` após splash; ver `app/main.py` e `splash_screen.py`.
2. **Pentaho KTR inválido** — substituir `<row-meta>` deve trocar o bloco inteiro (`<row-meta>...</row-meta>`), não só o interior (bug já corrigido em `pentaho_fields.py`).
3. **Layout Spoon “torto”** — perfis em `pentaho_layout.py` (`ems2unit` vs `esp2unit` vs `non_multi`); não reutilizar coordenadas de um template em outro.
4. **Job com nome `Transformation`** — normalizar para `dtf_{Entidade}` via `normalize_job_transformation_entry`.
5. **OpenEdge sem `SKIP`** — paginação de preview usa estratégia compatível em `odbc_client` (não assumir SQL Server).
6. **Histórico / TclError** — não destruir widgets do painel de histórico; usar `grid_remove` (`history_panel.py`).

---

## Checklist antes de encerrar uma tarefa

- [ ] Escopo mínimo; sem alterações colaterais não pedidas
- [ ] `ruff` / testes relevantes passando
- [ ] Textos de UI em português, consistentes com telas existentes
- [ ] Se mexer em Pentaho: validar XML bem formado e layout do perfil correto
- [ ] **`CHANGELOG.md`** atualizado na versão atual (obrigatório em entrega relevante)
- [ ] **Bump** (`bump_version.py`) só se este lote fecha uma nova release após o último commit versionado (ver [Versionamento](docs/ai/CONVENTIONS.md#versionamento))
- [ ] Não commitar `.env`, `dist/`, `build/`, `build_32b/`, `build_64b/`, `.mypy_cache/`
- [ ] Se Fase 1 SSIS: `docs/ai/SSIS.md` + etapa correspondente em `TODO.md`
- [ ] Se Fase 2 web: checklist inteiro do TODO + breaking change no CHANGELOG
- [ ] Atualizar `docs/ai/*` ou `AGENTS.md` só se mudou arquitetura ou contratos importantes

---

## Idioma

- **Português** para: UI, docs, `CHANGELOG.md`, **commits**, PRs e respostas ao desenvolvedor (salvo pedido de inglês).
- **Inglês** para: nomes de código (funções, módulos) quando o arquivo já usa inglês; prefixos de tipo de commit (`feat:`, `fix:`) são opcionais — a **descrição** fica em português.
- Detalhes e exemplos: [CONVENTIONS.md — Idioma](docs/ai/CONVENTIONS.md#idioma).
