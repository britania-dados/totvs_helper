# Totvs Helper

Ferramenta desktop em Python para apoiar a criação de cargas ETL de tabelas TOTVS (Progress/OpenEdge), gerando scripts de apoio para SQL Server e SSIS.

**Desenvolvido para [Britânia Eletrodomésticos](https://www.britania.com.br/).**

## Distribuição interna (Britânia)

O executável (**`TotvsHelper.exe`**) e o arquivo **`.env`** (credenciais ODBC) usados no dia a dia ficam na rede interna da Britânia, no diretório:

`P:\TECNOLOGIA DA INFORMACAO\SISTEMAS\Desenvolvimento TI\Desenvolvimento Externo\dados\TOTVS HELPER`

- Execute o programa a partir desse caminho (ou atalho apontando para ele).
- Alterações de credenciais devem ser feitas no `.env` dessa pasta; o arquivo **não** é versionado neste repositório.
- Para desenvolvimento ou novo build, use `.env.example` na raiz do projeto como modelo.

Logs da aplicação (rotativos): `%APPDATA%\TotvsHelper\logs\totvs_helper.log`

## Interface (CustomTkinter)

A aplicação usa uma **única janela** com fluxo em etapas, sem precisar fechar e reabrir o programa:

1. **Conexão ODBC** — lista DSNs OpenEdge com busca; conecta e carrega tabelas.
2. **Tabela e opções** — busca de tabela, campos livres e multi-empresa; botão **Voltar** retorna ao passo 1.
3. **Scripts gerados** — abas (Query ETL, Diferencial SSIS, DDL, UPDATE, DELETE) com **Copiar aba** e **Salvar TXT**.

Ações globais: **Novo processo** (reinicia o fluxo mantendo o app aberto), **Voltar** entre etapas e **Sair**.

```mermaid
flowchart LR
    dsnStep[EtapaDSN] --> tableStep[EtapaTabela]
    tableStep --> resultsStep[EtapaResultados]
    resultsStep -->|"NovoProcesso"| dsnStep
    tableStep -->|"Voltar"| dsnStep
    resultsStep -->|"Voltar"| tableStep
    appMain[app.main] --> uiApp[ui.app_window]
    appMain --> odbcClient[infra.odbc_client]
    appMain --> scriptGenerator[services.script_generator]
```

Layout com **sidebar lateral** (Conexão, Tabela, Scripts, Histórico), cards no conteúdo principal e acento visual Britânia.

Recursos da interface:

- Syntax highlighting SQL (Pygments) nas abas de resultado
- Toasts no canto inferior direito (sucesso, erro, aviso)
- Pré-visualização de campos, PK e grade de dados (todas as colunas com scroll; páginas de 10 registros)
- Histórico da sessão com restauração sem reconectar
- Configurações (`Ctrl+,`): tema escuro/claro/sistema, pasta padrão de exportação
- Atalhos: `Enter`, `Esc`, `Ctrl+C`, `Ctrl+Shift+C`, `Ctrl+S`, `Ctrl+Tab` / `Ctrl+Shift+Tab` (abas de script), `F5`
- Splash ao abrir o `.exe`: imagem nativa do PyInstaller durante a extração + janela de progresso até a interface principal
- Overlay de carregamento, listas performáticas, banner de erros inline

Stack: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) + [Pygments](https://pygments.org/).

## Principais funcionalidades

- Lista DSNs ODBC do tipo OpenEdge com filtro de busca
- Permite selecionar tabela TOTVS e opções de geração
- Gera:
  - query para ETL
  - DDL de `CREATE TABLE`
  - scripts de `UPDATE` e `DELETE`
  - expressão de diferencial para SSIS
- Exporta todos os helpers para `.txt` ou copia por aba
- Navegação entre etapas sem reiniciar o executável

## Requisitos

- Windows com ODBC OpenEdge configurado
- Python 3.9
- DSN válido no ODBC (`odbcad32.exe`)

## Estrutura do projeto

```text
totvs_helper/
  main.py
  assets/
  scripts/
  src/
    totvs_helper/
      app/
      config/
      infra/
      services/
      ui/
  tests/
  totvs_helper.spec
```

## Configuração de ambiente

1. Copie o exemplo de ambiente:

```powershell
copy .env.example .env
```

2. Preencha as credenciais no `.env`:

- `TOTVS_ODBC_USER_PRIMARY`
- `TOTVS_ODBC_PASSWORD_PRIMARY`
- `TOTVS_ODBC_USER_FALLBACK`
- `TOTVS_ODBC_PASSWORD_FALLBACK`
- `TOTVS_ODBC_TIMEOUT`

Em produção na Britânia, o `.env` efetivo é o da pasta de rede citada acima.

## Instalação

Crie e ative um ambiente virtual, depois instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```powershell
python main.py
```

## Qualidade e testes

Instale dependências de desenvolvimento:

```powershell
pip install -r requirements-dev.txt
```

Comandos:

```powershell
ruff check .
black --check .
pytest
pytest --cov=src/totvs_helper
mypy src
```

Atalhos locais:

```powershell
make lint
make format
make test
make typecheck
make build
```

## Build do executável (.exe)

O build é feito com PyInstaller para manter o processo reproduzível.
O arquivo `.env` da raiz é embutido no executável durante o build.
O build também inclui metadados de versão Windows e ícone da aplicação.

O ícone oficial fica em `assets/totvs_helper_logo.png` e é convertido para
`assets/totvs_helper.ico` automaticamente no build.

```powershell
.\scripts\build_exe.ps1
```

Opcionalmente, build direto com o spec versionado:

```powershell
python -m PyInstaller --clean --noconfirm totvs_helper.spec
```

Artefatos locais do build (ignorados pelo Git):

- `dist/TotvsHelper.exe` — executável gerado
- `build/` — arquivos temporários de build

Após validar o build, copie `TotvsHelper.exe` (e atualize o `.env` se necessário) para a pasta de rede da Britânia indicada na seção [Distribuição interna](#distribuição-interna-britânia).

## Troubleshooting

- **Sem DSN na lista:** valide se o driver OpenEdge está instalado e o DSN foi criado.
- **Falha de autenticação:** valide usuário/senha no `.env` da rede (ou gere novo `.exe` com `.env` atualizado no build).
- **Erro de conexão:** teste o DSN via `odbcad32.exe`.
- **Logs:** consulte `%APPDATA%\TotvsHelper\logs\totvs_helper.log`.
- **Quero outra tabela:** use **Voltar** na etapa de resultados ou **Novo processo** para trocar o DSN.
- **Interface travada:** aguarde o fim da conexão/geração (operações ODBC rodam em segundo plano).

## Roadmap

- Melhorar segurança das credenciais com Windows DPAPI.
- Permitir múltiplos perfis de conexão DSN por ambiente.
- Expandir testes de regressão para mais tabelas de referência.
