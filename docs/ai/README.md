# Documentação para IA e desenvolvedores

Estes arquivos orientam **Cursor**, **Claude Code** e outros agentes de código a trabalhar no Totvs Helper com contexto correto.

## Por onde começar

1. **[AGENTS.md](../../AGENTS.md)** — entrada rápida, mapa do repo, checklist, armadilhas.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — camadas, fluxo, onde alterar código.
3. **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** — domínio, fluxos, módulos.
4. **[CONVENTIONS.md](CONVENTIONS.md)** — Python, UI, testes, git, **idioma** (incl. commits em português), versionamento, **changelog**.
5. **[CHANGELOG.md](../../CHANGELOG.md)** — histórico de versões (**obrigatório atualizar** nas entregas).
6. **[PENTAHO.md](PENTAHO.md)** — export PDI 9.4 (somente se for mexer em cargas Pentaho).

## Cursor IDE

Regras automáticas em [`.cursor/rules/`](../../.cursor/rules/):

| Regra | Escopo |
|-------|--------|
| `totvs-helper-core.mdc` | Sempre ativa |
| `python-services.mdc` | `src/totvs_helper/services/` |
| `python-ui.mdc` | `src/totvs_helper/ui/` |
| `pentaho-templates.mdc` | Templates + `pentaho_*.py` |
| `tests.mdc` | `tests/` |

## Outros agentes

- **Claude Code / CLI:** inclua `AGENTS.md` no contexto ou peça para ler `docs/ai/`.
- **GitHub Copilot:** pode usar `AGENTS.md` (convenção suportada em vários repos).

## Roadmap

Planejamento em **[TODO.md](../../TODO.md)**:

- **Fase 1:** exportação SSIS (`.dtsx`) no desktop — etapas incrementais.
- **Fase 2:** app web no Ubuntu (JDBC + HTMX) — **entrega única**; ver checklist no TODO.

Ao concluir uma etapa ou fase, marque checkboxes no `TODO.md` e atualize o CHANGELOG.

## Manutenção

Atualize esta pasta quando:

- Mudar arquitetura (novas camadas, fluxo UI ou web).
- Concluir Fase 1: criar `docs/ai/SSIS.md` (como `PENTAHO.md`).
- Concluir Fase 2: ARCHITECTURE, README, AGENTS (desktop → web).
- Alterar contratos de `ScriptGenerator`, Pentaho ou SSIS.

Sempre que a mudança for entregável: registro em **[CHANGELOG.md](../../CHANGELOG.md)** na versão atual. **`python scripts/bump_version.py X.Y.Z`** só ao fechar um novo lote **depois** do commit da versão anterior — não a cada tarefa (regras em [CONVENTIONS.md — Versionamento](CONVENTIONS.md#versionamento)).

O [README.md](../../README.md) permanece focado em instalação e uso humano.
