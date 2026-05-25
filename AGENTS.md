# Guia para agentes de IA (Cursor, Claude Code, etc.)

Este arquivo é o ponto de entrada para assistentes de código trabalharem no **Totvs Helper**. Leia-o antes de alterar o repositório.

Documentação complementar:

| Documento | Conteúdo |
|-----------|----------|
| [README.md](README.md) | Instalação, build, uso humano, troubleshooting |
| [docs/ai/PROJECT_CONTEXT.md](docs/ai/PROJECT_CONTEXT.md) | Domínio, arquitetura, fluxos, módulos |
| [docs/ai/CONVENTIONS.md](docs/ai/CONVENTIONS.md) | Padrões de código, testes, git, o que evitar |
| [docs/ai/PENTAHO.md](docs/ai/PENTAHO.md) | Geração de cargas PDI 9.4 (`.kjb` / `.ktr`) |
| [TODO.md](TODO.md) | Roadmap (próximo: **carga SSIS**) |

Regras Cursor (aplicadas automaticamente no IDE): `.cursor/rules/*.mdc`

---

## O que é o projeto

**Totvs Helper** é um app desktop Windows (Python 3.9) que conecta em bancos **TOTVS / OpenEdge** via ODBC, lê metadados de tabelas e gera artefatos ETL:

- Scripts SQL (query ETL, DDL, UPDATE, DELETE, diferencial SSIS)
- Exportação Pentaho PDI 9.4 (`wkf_*.kjb` + `dataflows/dtf_*.ktr`)

**Não** executa ETL, **não** conecta em SQL Server de produção para carga — apenas gera arquivos.

**Cliente / contexto:** Britânia Eletrodomésticos. UI em português; mensagens de erro e labels para usuário final em PT-BR.

**Versão atual:** `src/totvs_helper/version.py` (`__version__`, hoje `2.1.0`). Sincronizar manualmente `packaging/windows_version_info.txt` no build se mudar versão.

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
- **Credenciais:** `.env` nunca commitar; build pode embutir `.env` no `.exe` (ver README).
- **Mudanças mínimas** — preferir diff focado; não refatorar fora do escopo.
- **Commits / push** só quando o usuário pedir explicitamente.

---

## Estrutura do repositório (mapa mental)

```text
totvs_helper/
  main.py                 # Entry: delega para totvs_helper.app.main.run
  src/totvs_helper/
    app/main.py           # Logging, splash, wiring ODBC + UI
    config/settings.py    # .env / variáveis ODBC
    infra/odbc_client.py  # DSN, tabelas, campos, PK, índices, amostra TOP 10
    services/
      script_generator.py   # SQL helpers (core)
      pentaho_*.py          # Export PDI (templates XML)
      txt_exporter.py
      constants.py          # Campos livres ignorados, etc.
    ui/
      app_window.py       # Orquestrador principal (estado, async, telas)
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
.\scripts\build_exe.ps1
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
- [ ] Não commitar `.env`, `dist/`, `build/`, `.mypy_cache/`
- [ ] Atualizar `docs/ai/*` ou `AGENTS.md` só se mudou arquitetura ou contratos importantes

---

## Idioma das respostas

Responder ao desenvolvedor em **português** (padrão do time), salvo se pedir inglês. Código: identificadores e comentários em inglês onde o arquivo já segue inglês; strings de UI em português.
