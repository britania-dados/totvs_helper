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
| [TODO.md](TODO.md) | Roadmap (próximo: **carga SSIS**) |

Regras Cursor (aplicadas automaticamente no IDE): `.cursor/rules/*.mdc`

---

## O que é o projeto

**Totvs Helper** é um app desktop Windows (Python 3.9) que conecta em bancos **TOTVS / OpenEdge** via ODBC, lê metadados de tabelas e gera artefatos ETL:

- Scripts SQL (query ETL, DDL, UPDATE, DELETE, diferencial SSIS)
- Exportação Pentaho PDI 9.4 (`wkf_*.kjb` + `dataflows/dtf_*.ktr`)

**Não** executa ETL, **não** conecta em SQL Server de produção para carga — apenas gera arquivos.

**Cliente / contexto:** Britânia Eletrodomésticos. UI em português; mensagens de erro e labels para usuário final em PT-BR.

**Versão atual:** `src/totvs_helper/version.py` (`__version__`, hoje `2.1.2`). Bump: `python scripts/bump_version.py X.Y.Z`. Ao bumpar, atualize também **`CHANGELOG.md`**.

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

**Fluxo UI (3 etapas):** DSN → Tabela/opções → Scripts (+ Pentaho). Estado em `SessionState`; operações ODBC em thread + `queue` para não travar UI.

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
| Export Pentaho | `services/pentaho_exporter.py`, `pentaho_fields.py`, `pentaho_layout.py`, `packaging/pentaho/templates/` |
| Versão / build | `version.py`, `packaging/windows_version_info.txt`, `totvs_helper.spec` |
| Próximo: SSIS | Ainda não existe — ver `TODO.md`; espelhar padrão Pentaho (serviço + UI + templates) |

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
- [ ] **`CHANGELOG.md` atualizado** (bugfix, feature, build, breaking change ou doc que muda processo do time)
- [ ] Não commitar `.env`, `dist/`, `build/`, `build_32b/`, `build_64b/`, `.mypy_cache/`
- [ ] Atualizar `docs/ai/*` ou `AGENTS.md` só se mudou arquitetura ou contratos importantes

---

## Idioma das respostas

Responder ao desenvolvedor em **português** (padrão do time), salvo se pedir inglês. Código: identificadores e comentários em inglês onde o arquivo já segue inglês; strings de UI em português.
