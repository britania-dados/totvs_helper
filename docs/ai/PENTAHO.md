# Pentaho PDI — geração de cargas

Referência para agentes de IA alterarem ou estenderem o exportador Pentaho (v2.1.0+).

---

## Objetivo

A partir dos metadados já carregados na sessão, gerar na pasta escolhida pelo usuário:

```text
wkf_{Entidade}.kjb
dataflows/dtf_{Entidade}.ktr
```

- **PDI 9.4**, modo **sync** apenas (`MergeRows` + `SynchronizeAfterMerge`).
- Destino: conexão `STAGE`, schema `tot`, tabela PascalCase.

---

## Módulos

| Arquivo | Responsabilidade |
|---------|------------------|
| `pentaho_constants.py` | Famílias DSN, branches multi, templates, `is_multi_company_dsn` |
| `pentaho_sql.py` | SQL Table Input OpenEdge, `format_entity_name`, escape XML |
| `pentaho_fields.py` | Rebuild colunas em CheckSum, SortRows, STAGE, row-meta, Sync |
| `pentaho_layout.py` | Coordenadas Spoon (`xloc`/`yloc`) por perfil |
| `pentaho_exporter.py` | Orquestra leitura template + escrita arquivos |

**UI:** botão na `ResultsScreen` → `app_window._generate_pentaho_load`.

**Templates:** `packaging/pentaho/templates/{multi_esp2unit,multi_ems2unit,non_multi_wms,non_multi_esp2corp}/`

Em runtime frozen: `sys._MEIPASS/packaging/pentaho/templates`.

---

## Regras de negócio

### Multi-empresa (`esp2unit`, `ems2unit`, `mov2unit`)

- 5 Table Inputs: BRIC, ECOM, ELETRO, NORDESTE, PHILCO.
- Literal `EMPRESA` por estabelecimento (`MULTI_BRANCHES`).
- PK de sync inclui `EMPRESA`.

### Não multi (`wms`, `esp2corp`)

- Campo **`BASE`** na projeção (`VAREJO`, `ECOM`, …).
- Uma tabela `tot.{Entidade}` — sem `dtf_ecom_*` separado.
- DDL/query do `ScriptGenerator` com `[BASE] varchar(8)` na PK quando `multi_company=False`.

### Família ems2unit (template `multi_ems2unit`)

Fluxo extra vs esp2unit:

- `Sort rows 2` → `SV DATASUL` → merge
- `STAGE` → `Sort rows` → `SV STAGE` → merge
- `InsereData` → `Select values` → `Synchronize after merge`

**Layout obrigatório:** perfil `ems2unit` em `pentaho_layout.py` (mapa copiado de `dtf_Item_depois.ktr`). Não misturar coordenadas do template esp2unit.

---

## Pipeline de transformação do KTR

Ordem em `apply_field_metadata` + exporter:

1. **SQL** — cada passo TableInput fonte + SQL do passo `STAGE` (SELECT colunas `[tot].[Entidade]`).
2. **CheckSum** — lista `<field><name>…</name></field>` com todas as colunas de negócio + EMPRESA/BASE.
3. **SortRows** — chaves = PK + EMPRESA/BASE.
4. **row-meta** — substituir bloco **inteiro** `<row-meta>…</row-meta>` (nunca duplicar tags).
5. **MergeRows / SynchronizeAfterMerge** — keys e values com todas as colunas + CHKSUM + DataCarga.

Depois: `apply_ktr_gui_layout` conforme `detect_layout_profile` (presença de `SV DATASUL` → ems2unit).

---

## Job KJB

`normalize_job_transformation_entry`:

- Nome do passo TRANS: `dtf_{Entidade}` (não `Transformation`).
- Hops `from`/`to` alinhados.
- `<transname>dtf_{Entidade}</transname>` (substituir `<transname/>` vazio).

`apply_job_gui_layout`: Start (240,352) → dtf (416,352) → Success/Abort.

---

## Adicionar / atualizar template

1. Obter `.kjb`/`.ktr` validados no Spoon 9.4.
2. Copiar para `packaging/pentaho/templates/<chave>/` como `wkf_TEMPLATE.kjb` e `dataflows/dtf_TEMPLATE.ktr`.
3. Manter nomes de passo consistentes com `MULTI_BRANCHES` / `NON_MULTI_BASES` ou atualizar constantes.
4. Registrar chave em `MULTI_TEMPLATE_BY_FAMILY` ou `NON_MULTI_TEMPLATE_BY_FAMILY`.
5. Se layout novo: adicionar mapa em `pentaho_layout.py` + teste em `tests/test_pentaho_layout.py`.
6. Testes: `tests/test_pentaho_exporter.py`, `tests/test_pentaho_fields.py`.

---

## Testes rápidos

```powershell
$env:PYTHONPATH = "src"
pytest tests/test_pentaho_layout.py tests/test_pentaho_exporter.py -q
```

Validação manual: abrir KTR/KJB no Spoon — diagrama alinhado, sem steps sobrepostos, job com nome `dtf_*`.

---

## Erros comuns

| Sintoma | Causa provável |
|---------|----------------|
| XML parse error `</step>` | row-meta duplicado |
| Steps sobrepostos | perfil de layout errado (ems2unit vs esp2unit) |
| Job mostra "Transformation" | falta `normalize_job_transformation_entry` |
| Colunas faltando no Sync | `apply_field_metadata` não rodou ou fields vazios |
| `SortRows 'SORT STAGE' not found` | template usa `Sort rows`; usar `discover_sort_step_names` (hops), não nomes fixos |
