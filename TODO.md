# TODO — Totvs Helper

Itens planejados após a versão **2.0.0** (interface, preview, histórico e índices).

## Próximo passo (prioridade alta): apoio a cargas Pentaho

Hoje o Totvs Helper gera scripts para **SQL Server** e a expressão de **diferencial SSIS**. O objetivo da próxima fase é ajudar montar e manter cargas no **Pentaho Data Integration (PDI)** com o mesmo fluxo DSN → tabela → metadados.

### Escopo sugerido

- [ ] **Nova aba ou seção “Pentaho”** nos scripts gerados, ao lado de Query ETL / Diferencial SSIS / DDL / UPDATE / DELETE.
- [ ] **Snippet de Table Input (origem OpenEdge)** — SQL de extração reutilizando a query ETL já gerada, com notas de conexão ODBC/JDBC compatível com o DSN usado no helper.
- [ ] **Snippet de Table Output / Insert-Update (destino SQL Server)** — mapeamento campo a campo (origem TOTVS → destino staging/warehouse), alinhado ao DDL `CREATE TABLE` existente.
- [ ] **Diferencial para Pentaho** — equivalente à aba “Diferencial SSIS”: expressão ou passo de comparação (hash / merge / `Merge Rows (diff)` / `Insert-Update`) usando PK e opção multi-empresa.
- [ ] **Exportação Pentaho-friendly** — incluir blocos Pentaho no `.txt` exportado e em “Copiar tudo”; opcionalmente template `.ktr` mínimo (XML) ou checklist de passos no Spoon.
- [ ] **Documentação** — README com exemplo de job simples (extração TOTVS → staging SQL Server) montado a partir dos artefatos do helper.

### Dependências / decisões

- [ ] Confirmar versão do Pentaho/PDI usada na Britânia (8.x / 9.x) e tipo de conexão na origem (ODBC OpenEdge vs JDBC).
- [ ] Alinhar nomenclatura de schemas/campos de destino (staging, `empresa`, convenções já usadas no SSIS).
- [ ] Validar com 2–3 tabelas reais (`mov2unit_*`, `ems2unit_*`) se os snippets batem com jobs existentes.

### Fora do escopo imediato (manter no backlog)

- [ ] Edição visual de `.ktr` / `.kjb` dentro do app.
- [ ] Execução de jobs Pentaho pelo Totvs Helper.
- [ ] Substituir completamente o fluxo SSIS (manter SSIS e Pentaho em paralelo).

