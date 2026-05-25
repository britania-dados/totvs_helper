# TODO — Totvs Helper

## Próximo: gerar carga SSIS

Gerar pacote/carga SSIS completa a partir dos scripts e metadados já produzidos pelo helper (query ETL, diferencial, DDL, UPDATE, DELETE).

### Escopo inicial (a detalhar)

- [ ] Definir template SSIS de referência (`.dtsx` / projeto) e pasta de saída
- [ ] Mapear substituições: conexões, SQL, colunas, PK, multi-empresa / `BASE`, campos livres
- [ ] Botão na tela de scripts (análogo à carga Pentaho)
- [ ] Testes com 2–3 tabelas de referência

### Fora do escopo (por enquanto)

- Execução de pacotes SSIS pelo Totvs Helper
- Editor visual de `.dtsx` no app
