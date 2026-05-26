# Convenções de desenvolvimento — Totvs Helper

Guia para humanos e agentes de IA manterem o código consistente.

---

## Idioma

O projeto é **em português** (padrão Britânia / time interno). Isso vale para artefatos voltados a pessoas, não para identificadores de código.

| O quê | Idioma |
|-------|--------|
| UI (labels, toasts, erros ao usuário) | **Português** (PT-BR) |
| [`CHANGELOG.md`](../../CHANGELOG.md) | **Português** |
| Documentação (`README`, `docs/ai/*`, `AGENTS.md`, `TODO.md`) | **Português** |
| **Mensagens de commit** | **Português** — assunto e corpo; frases completas; foco no *porquê* |
| **Descrições de PR** (título e corpo) | **Português**, no mesmo espírito do commit |
| Respostas de agentes de IA ao desenvolvedor | **Português**, salvo pedido explícito de inglês |
| Código (nomes de módulos/funções/variáveis) | **Inglês** onde o arquivo já segue inglês |
| Comentários no código | Inglês ou português conforme o arquivo; preferir o idioma já usado no arquivo |

### Commits e PRs

- **Não** usar inglês no título do commit só por hábito (`feat: add feature`); alinhar ao histórico do repositório.
- Formato habitual: `tipo: versão X.Y.Z — resumo` ou `tipo: resumo` (ex.: `feat: versão 2.1.4 — chaves ECOM emitente`).
- Tipos comuns: `feat`, `fix`, `docs`, `refactor`, `test` (prefixo em inglês é aceitável; **descrição em português**).

---

## Python

- **3.9** — `pyproject.toml` fixa `target-version = py39`.
- **Formatação:** Black (line-length 88), Ruff (E, F, I, W).
- **Tipos:** preferir type hints em código novo; mypy é permissivo (`disallow_untyped_defs = false`).
- **Imports:** ordem isort via Ruff; pacote em `src/totvs_helper`.
- **`from __future__ import annotations`** em módulos novos quando fizer sentido.

### Estilo de mudança

- Diff **mínimo** e focado no pedido.
- Reutilizar padrões existentes (`IconButton`, `SessionState`, `_run_async` em `app_window`).
- Evitar abstrações prematuras (helpers de uma linha, factories desnecessárias).
- Comentários só para lógica não óbvia (OpenEdge, XML Pentaho, Tk quirks).

---

## UI (CustomTkinter)

- Tokens visuais: `ui/design_tokens.py`, `ui/theme.py` (cores Britânia).
- Textos de label/botão/toast em **português**.
- Operações longas: usar `_run_async` + loading overlay; nunca bloquear `mainloop` com ODBC.
- Widgets reutilizáveis em `ui/widgets/`; telas em `ui/screens/`.
- Ao destruir/recriar widgets: preferir `grid_remove()` / `grid()` em vez de `destroy()` se o container permanece (lição do `HistoryPanel`).

### Tk / CTk

- Fontes CTk exigem root Tk válido — ver splash handoff em `app/main.py`.
- Testes de UI são limitados (ambiente headless); testar lógica em serviços quando possível.

---

## Testes

- Framework: **pytest**, `pythonpath = src` no `pyproject.toml`.
- Nomear `test_<módulo>.py`; funções `test_<comportamento>`.
- SQL estável: comparar com `tests/expected/` quando aplicável.
- Pentaho: testes sem Spoon — validar substring XML, contagem de steps, `xml.etree.ElementTree.fromstring` para KTR gerado.
- Não adicionar testes triviais que só repetem mocks.
- Rodar `pytest` antes de concluir tarefas de código.

### Executar subset

```powershell
$env:PYTHONPATH = "src"
pytest tests/test_script_generator.py tests/test_pentaho_exporter.py -q
```

---

## Git

- **Não commitar** sem pedido explícito do usuário.
- **Nunca** commitar `.env`, credenciais, `dist/`, `build/`, `build_32b/`, `build_64b/`, `.mypy_cache/`.
- **Idioma:** commits e PRs em **português** — ver [Idioma](#idioma).
- Não `git push --force` em `main`/`master`.
- Não alterar `git config`.

---

## Versionamento

- Fonte única: `src/totvs_helper/version.py` → `__version__`.
- Comando: `python scripts/bump_version.py X.Y.Z` (atualiza `version.py` e `packaging/windows_version_info.txt`). O build gera `windows_version_info.build.txt` no spec.
- `pyproject.toml` usa version dinâmica do attr acima.

### Quando subir a versão (PATCH / MINOR / MAJOR)

`__version__` em `version.py` é a **versão do último commit versionado** (release fechada). **Não** incrementar o PATCH a cada solicitação, tarefa de agente ou PR intermediário.

| Momento | O que fazer |
|---------|-------------|
| **Durante o ciclo** (várias alterações ainda sem commit da próxima versão) | Registrar mudanças em [`CHANGELOG.md`](../../CHANGELOG.md) na seção **`## X.Y.Z` atual** (ex.: `2.1.4`). **Não** rodar `bump_version.py`. |
| **Ao fechar um novo lote entregável**, depois do commit que encerrou a versão anterior | **Uma vez:** `python scripts/bump_version.py X.Y.Z` + seção `## X.Y.Z` no changelog (se ainda não existir). Tipicamente junto ao commit que entrega o lote, ou quando o usuário pedir commit/release. |

| Tipo de entrega | Incremento | Exemplo |
|-----------------|--------------|---------|
| Bugfix, ajuste de doc de processo, checklist | **PATCH** (`Z`) | `2.1.3` → `2.1.4` (um PATCH por lote, não por tarefa) |
| Feature nova (ex.: export SSIS) | **MINOR** (`Y`) | `2.1.4` → `2.2.0` |
| Breaking change (ex.: desktop → web) | **MAJOR** (`X`) | `2.2.0` → `3.0.0` |

Fluxo ao encerrar uma tarefa **no meio do ciclo** (ainda sem novo release):

1. Implementar a mudança.
2. Atualizar a seção da versão **atual** em [`CHANGELOG.md`](../../CHANGELOG.md) (bullets em Adicionado/Alterado/Corrigido).
3. **Não** alterar `version.py` se já houve bump no commit anterior e este lote ainda não foi commitado como nova versão.

Fluxo ao **fechar** um lote para commit/release (após o commit da versão anterior):

1. Consolidar entradas no changelog.
2. Definir `X.Y.Z` (na dúvida, **PATCH**).
3. `python scripts/bump_version.py X.Y.Z`
4. Commit (quando o usuário pedir) com `version.py`, `CHANGELOG.md` e o código do lote.

**Não** fazer bump por typos em comentário sem efeito para usuário/dev. **Não** fazer dois PATCH seguidos (`2.1.4` → `2.1.5` → `2.1.6`) no mesmo ciclo sem commit intermediário que fechou `2.1.4`.

## Changelog

**Obrigatório** manter [`CHANGELOG.md`](../../CHANGELOG.md) alinhado ao trabalho em andamento: bullets na versão atual durante o ciclo; ao subir versão, a seção `## X.Y.Z` nova coincide com o bump.

Inclua entradas na seção da versão em edição (`## X.Y.Z` atual ou recém-criada após `bump_version.py`), usando as categorias já adotadas:

| Categoria | Quando usar |
|-----------|-------------|
| **Adicionado** | Feature nova, script, tela, exportador, teste relevante |
| **Alterado** | Comportamento, build, refatoração com impacto para quem usa/mantém |
| **Corrigido** | Bugfix |
| **Removido** | API, flag, arquivo ou fluxo descontinuado |

**Não precisa** changelog para typos isolados em comentário ou ajuste puramente interno sem efeito para usuário/dev — use critério; na dúvida, registre.

Agentes de IA: **changelog** em toda entrega relevante; **bump de versão** só ao fechar lote pós-commit da versão anterior (não a cada prompt). `ruff` e `pytest` nos módulos alterados continuam obrigatórios.

---

## Segurança

- Credenciais só em `.env` ou variáveis documentadas em `.env.example`.
- Não logar senhas.
- Build embute `.env` — avisar usuário se pedirem commit de secrets.

---

## Documentação

- README: usuário final + dev setup.
- **`CHANGELOG.md`:** histórico de versões — **atualizar em toda entrega relevante** (ver seção [Changelog](#changelog) acima).
- `docs/ai/*` + `AGENTS.md`: agentes e onboarding técnico.
- `TODO.md`: roadmap oficial (Fase 1 SSIS incremental; Fase 2 web entrega única); não duplicar o plano longo no README — só resumo e link.

Ao mudar arquitetura ou contratos públicos entre módulos, atualizar `docs/ai/PROJECT_CONTEXT.md` ou `AGENTS.md`.

---

## O que não fazer sem alinhamento

- Refatoração ampla da UI ou troca de framework.
- Suporte Linux/macOS como alvo principal.
- Executar jobs Pentaho/SSIS de dentro do app.
- Gerar cargas Pentaho **full/truncate** ou `dtf_ecom_*` paralelos (fora do padrão atual).
- Dependências novas pesadas sem necessidade clara.
