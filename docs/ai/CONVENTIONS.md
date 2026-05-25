# Convenções de desenvolvimento — Totvs Helper

Guia para humanos e agentes de IA manterem o código consistente.

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
- **Nunca** commitar `.env`, credenciais, `dist/`, `build/`, `.mypy_cache/`.
- Mensagens de commit em **português**, frases completas (foco no porquê).
- Não `git push --force` em `main`/`master`.
- Não alterar `git config`.

---

## Versionamento

- Fonte única: `src/totvs_helper/version.py` → `__version__`.
- Atualizar `packaging/windows_version_info.txt` ao bump de versão para o `.exe`.
- `pyproject.toml` usa version dinâmica do attr acima.

---

## Segurança

- Credenciais só em `.env` ou variáveis documentadas em `.env.example`.
- Não logar senhas.
- Build embute `.env` — avisar usuário se pedirem commit de secrets.

---

## Documentação

- README: usuário final + dev setup.
- `docs/ai/*` + `AGENTS.md`: agentes e onboarding técnico.
- `TODO.md`: roadmap; não duplicar roadmap longo no README.

Ao mudar arquitetura ou contratos públicos entre módulos, atualizar `docs/ai/PROJECT_CONTEXT.md` ou `AGENTS.md`.

---

## O que não fazer sem alinhamento

- Refatoração ampla da UI ou troca de framework.
- Suporte Linux/macOS como alvo principal.
- Executar jobs Pentaho/SSIS de dentro do app.
- Gerar cargas Pentaho **full/truncate** ou `dtf_ecom_*` paralelos (fora do padrão atual).
- Dependências novas pesadas sem necessidade clara.
