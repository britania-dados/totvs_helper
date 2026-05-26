# Documentação para IA e desenvolvedores

Estes arquivos orientam **Cursor**, **Claude Code** e outros agentes de código a trabalhar no Totvs Helper com contexto correto.

## Por onde começar

1. **[AGENTS.md](../../AGENTS.md)** — entrada rápida, mapa do repo, checklist, armadilhas.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** — camadas, fluxo, onde alterar código.
3. **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** — domínio, fluxos, módulos.
4. **[CONVENTIONS.md](CONVENTIONS.md)** — Python, UI, testes, git, versionamento, **changelog**.
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

## Manutenção

Atualize esta pasta quando:

- Mudar arquitetura (novas camadas, fluxo UI).
- Adicionar exportador (ex.: SSIS).
- Alterar contratos de `ScriptGenerator` ou Pentaho.

Sempre que a mudança for entregável ao time ou ao usuário, registre também em **[CHANGELOG.md](../../CHANGELOG.md)** (regra detalhada em [CONVENTIONS.md](CONVENTIONS.md#changelog)).

O [README.md](../../README.md) permanece focado em instalação e uso humano.
