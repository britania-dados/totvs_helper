"""ODBC client for TOTVS Progress metadata and queries."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pyodbc
from pyodbc import Connection, Cursor, Row

from totvs_helper.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableIndexRow:
    """One field belonging to an index on a table."""

    index_name: str
    field_name: str
    field_order: int
    is_unique: bool
    is_primary: bool


class OdbcClient:
    """Encapsulates ODBC operations against Progress/OpenEdge."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._table_recids: dict[str, str] = {}

    @staticmethod
    def list_odbcs() -> List[str]:
        """List ODBC data sources that use OpenEdge driver (A–Z)."""
        data_sources = pyodbc.dataSources()
        names = [
            name for name, driver in data_sources.items() if "OpenEdge" in driver
        ]
        return sorted(names, key=str.lower)

    def connect(self, data_source: str) -> Connection:
        """Connect to the given DSN with primary and fallback credentials."""
        attempts = [
            (self._settings.odbc_user_primary, self._settings.odbc_password_primary),
            (self._settings.odbc_user_fallback, self._settings.odbc_password_fallback),
        ]

        last_error: Optional[Exception] = None
        for user, password in attempts:
            try:
                connection_string = f"DSN={data_source};Uid={user};Pwd={password};"
                return pyodbc.connect(
                    connection_string, timeout=self._settings.odbc_timeout_seconds
                )
            except pyodbc.Error as exc:
                last_error = exc
                logger.warning(
                    "Falha ao conectar no DSN %s com usuario %s",
                    data_source,
                    user,
                )

        logger.error(
            "Tentativas de conexao esgotadas para DSN %s. Ultimo erro: %s",
            data_source,
            last_error,
        )
        raise ConnectionError(
            f"Falha ao conectar no DSN '{data_source}'. Verifique credenciais e DSN."
        ) from last_error

    def list_fields_and_pk(
        self, recid_table: str, connection: Connection
    ) -> Tuple[list[Row], list[str]]:
        """Return table fields metadata and PK field names."""
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    C."_field-name"
                    , C."_Data-Type"
                    , C."_Width"
                    , C."_Decimals"
                    , C."_Fetch-Type"
                FROM PUB."_field" C
                WHERE C."_file-recid" = ?
                ORDER BY C."_Order"
                WITH (NOLOCK)
                """,
                recid_table,
            )
            rows = cursor.fetchall()
            pk_fields = self._list_pk_fields(cursor, recid_table)
            return rows, pk_fields
        except pyodbc.Error as exc:
            raise RuntimeError("Erro ao listar campos da tabela selecionada.") from exc
        finally:
            cursor.close()

    @staticmethod
    def _normalize_rowid(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("latin-1", errors="replace")
        return str(value)

    def _store_table_rows(self, rows: list) -> List[str]:
        """Build recid map from (_File-Name, ROWID) rows; skip blank names."""
        recids: dict[str, str] = {}
        for row in rows:
            name = str(row[0]).strip()
            if not name:
                continue
            recids[name] = self._normalize_rowid(row[1])
        self._table_recids = recids
        return sorted(self._table_recids.keys(), key=str.lower)

    @staticmethod
    def _list_tables_via_catalog(cursor: Cursor) -> list:
        """Fallback using ODBC metadata when PUB._file queries return nothing."""
        rows: list = []
        for entry in cursor.tables(tableType="TABLE"):
            schema = (entry.table_schem or "").strip()
            name = (entry.table_name or "").strip()
            if not name:
                continue
            if schema and schema.upper() not in ("PUB", ""):
                continue
            rows.append((name, ""))
        return rows

    def list_tables(self, connection: Connection) -> List[str]:
        """Return visible table names and store ROWID mapping."""
        cursor = connection.cursor()
        queries = (
            (
                "hidden=0",
                """
                SELECT "_File-Name", ROWID
                FROM PUB."_file"
                WHERE "_Hidden" = 0
                WITH (NOLOCK)
                """,
            ),
            (
                "hidden null",
                """
                SELECT "_File-Name", ROWID
                FROM PUB."_file"
                WHERE "_Hidden" = 0 OR "_Hidden" IS NULL
                WITH (NOLOCK)
                """,
            ),
            (
                "tbl-type T",
                """
                SELECT "_File-Name", ROWID
                FROM PUB."_file"
                WHERE "_tbl-type" = 'T'
                WITH (NOLOCK)
                """,
            ),
            (
                "all files",
                """
                SELECT "_File-Name", ROWID
                FROM PUB."_file"
                WITH (NOLOCK)
                """,
            ),
        )
        try:
            rows: list = []
            for label, sql in queries:
                cursor.execute(sql)
                rows = cursor.fetchall()
                if rows:
                    logger.info(
                        "Tabelas carregadas via consulta '%s' (%s linhas).",
                        label,
                        len(rows),
                    )
                    break
                logger.warning(
                    "Consulta de tabelas '%s' retornou vazio; tentando alternativa.",
                    label,
                )

            if not rows:
                catalog_rows = self._list_tables_via_catalog(cursor)
                if catalog_rows:
                    logger.info(
                        "Tabelas carregadas via catálogo ODBC (%s linhas).",
                        len(catalog_rows),
                    )
                    self._table_recids = {
                        name: recid for name, recid in catalog_rows
                    }
                    return sorted(self._table_recids.keys(), key=str.lower)

            return self._store_table_rows(rows)
        except pyodbc.Error as exc:
            raise RuntimeError("Erro ao listar tabelas do banco TOTVS.") from exc
        finally:
            cursor.close()

    def get_table_recid(self, selected_table: str) -> str:
        """Return ROWID for selected table."""
        if not selected_table or not selected_table.strip():
            raise KeyError("Tabela selecionada invalida.")

        if selected_table not in self._table_recids:
            raise KeyError(
                f"Tabela '{selected_table}' nao encontrada na lista carregada."
            )
        return self._normalize_rowid(self._table_recids[selected_table])

    def test_connection(self, data_source: str) -> None:
        """Open and close a connection to validate DSN/credentials."""
        connection = self.connect(data_source)
        connection.close()

    def fetch_sample_rows(
        self,
        table_name: str,
        fields: Sequence[Sequence],
        connection: Connection,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[str], List[Tuple]]:
        """Return column names and a page of rows (offset via TOP + slice)."""
        if not fields:
            return [], []

        columns = [str(field[0]) for field in fields]
        projections = ", ".join(f'"{name}"' for name in columns)
        row_offset = max(0, int(offset))
        page_size = max(1, int(limit))
        fetch_top = row_offset + page_size
        sql = (
            f"SELECT TOP {fetch_top} {projections} "
            f'FROM PUB."{table_name}" WITH (NOLOCK)'
        )

        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            all_rows = [tuple(row) for row in cursor.fetchall()]
            page_rows = all_rows[row_offset : row_offset + page_size]
            return columns, page_rows
        except pyodbc.Error as exc:
            raise RuntimeError(
                f"Erro ao buscar amostra da tabela '{table_name}'."
            ) from exc
        finally:
            cursor.close()

    @staticmethod
    def _fetch_prime_index_recid(cursor: Cursor, recid_table: str) -> Optional[str]:
        """Return ROWID of the table primary index from PUB._file._prime-index."""
        try:
            cursor.execute(
                """
                SELECT F."_prime-index"
                FROM PUB."_file" F
                WHERE F.ROWID = ?
                WITH (NOLOCK)
                """,
                recid_table,
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                return None
            return OdbcClient._normalize_rowid(row[0])
        except pyodbc.Error:
            logger.debug(
                "Nao foi possivel ler _prime-index; primario sera inferido pela PK.",
                exc_info=True,
            )
            return None

    @staticmethod
    def _build_index_rows(
        rows: list,
        *,
        pk_set: set[str],
        prime_index_recid: Optional[str],
        has_sequence: bool,
        index_recid_col: Optional[int] = None,
    ) -> List[TableIndexRow]:
        """Normalize ODBC rows into TableIndexRow entries."""
        index_fields: dict[str, list[str]] = {}
        index_unique: dict[str, bool] = {}
        index_primary_flag: dict[str, bool] = {}
        index_order: dict[tuple[str, str], int] = {}
        index_recids: dict[str, str] = {}
        fallback_order: dict[str, int] = {}

        for row in rows:
            name = str(row[0]).strip()
            if not name:
                continue
            is_unique = bool(row[1])
            if has_sequence:
                order = int(row[2]) if row[2] is not None else 0
                field_name = str(row[3]).strip()
            else:
                order = fallback_order.get(name, 0)
                fallback_order[name] = order + 1
                field_name = str(row[2]).strip()

            if not field_name:
                continue

            index_unique[name] = is_unique
            index_fields.setdefault(name, []).append(field_name)
            index_order[(name, field_name)] = order

            if index_recid_col is not None and len(row) > index_recid_col:
                index_recids[name] = OdbcClient._normalize_rowid(row[index_recid_col])

        if prime_index_recid:
            for name, recid in index_recids.items():
                if recid == prime_index_recid:
                    index_primary_flag[name] = True

        for name, fields in index_fields.items():
            if name not in index_primary_flag and pk_set:
                if {str(f) for f in fields} == pk_set:
                    index_primary_flag[name] = True

        result: List[TableIndexRow] = []
        for name in sorted(index_fields.keys()):
            is_unique = index_unique.get(name, False)
            is_primary = index_primary_flag.get(name, False)
            for field_name in index_fields[name]:
                result.append(
                    TableIndexRow(
                        index_name=name,
                        field_name=field_name,
                        field_order=index_order.get((name, field_name), 0),
                        is_unique=is_unique,
                        is_primary=is_primary,
                    )
                )
        return result

    def list_table_indexes(
        self,
        recid_table: str,
        connection: Connection,
        pk_fields: Optional[List[str]] = None,
    ) -> List[TableIndexRow]:
        """Return index fields with unique/primary flags for the table."""
        cursor = connection.cursor()
        pk_set = {str(name) for name in (pk_fields or [])}
        prime_index_recid = self._fetch_prime_index_recid(cursor, recid_table)

        # Same joins as _list_pk_fields; variants differ by column names / filters.
        queries: Tuple[Tuple[str, str, bool, bool], ...] = (
            (
                "pk-style+seq",
                """
                SELECT
                    I."_Index-Name",
                    I."_Unique",
                    IC."_index-seq",
                    C."_Field-Name"
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                    AND I."_Active" = 1
                ORDER BY I."_Index-Name", IC."_index-seq"
                WITH (NOLOCK)
                """,
                True,
                False,
            ),
            (
                "pk-style",
                """
                SELECT
                    I."_Index-Name",
                    I."_Unique",
                    C."_Field-Name"
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                    AND I."_Active" = 1
                ORDER BY I."_Index-Name"
                WITH (NOLOCK)
                """,
                False,
                False,
            ),
            (
                "meta-lowercase+seq",
                """
                SELECT
                    I."_index-name",
                    I."_Unique",
                    IC."_index-seq",
                    C."_field-name"
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                ORDER BY I."_index-name", IC."_index-seq"
                WITH (NOLOCK)
                """,
                True,
                False,
            ),
            (
                "meta-lowercase",
                """
                SELECT
                    I."_index-name",
                    I."_Unique",
                    C."_field-name"
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                ORDER BY I."_index-name"
                WITH (NOLOCK)
                """,
                False,
                False,
            ),
            (
                "legacy-order",
                """
                SELECT
                    I."_Index-Name",
                    I."_Unique",
                    IC."_Order",
                    C."_Field-Name"
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                ORDER BY I."_Index-Name", IC."_Order"
                WITH (NOLOCK)
                """,
                True,
                False,
            ),
            (
                "with-index-rowid",
                """
                SELECT
                    I."_index-name",
                    I."_Unique",
                    IC."_index-seq",
                    C."_field-name",
                    I.ROWID
                FROM PUB."_Index" I
                    INNER JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    INNER JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WHERE I."_file-recid" = ?
                ORDER BY I."_index-name", IC."_index-seq"
                WITH (NOLOCK)
                """,
                True,
                True,
            ),
        )

        last_error: Optional[Exception] = None
        try:
            for label, sql, has_sequence, include_index_recid in queries:
                try:
                    cursor.execute(sql, recid_table)
                    rows = cursor.fetchall()
                except pyodbc.Error as exc:
                    last_error = exc
                    logger.debug(
                        "Consulta de índices '%s' falhou; tentando alternativa.",
                        label,
                        exc_info=True,
                    )
                    continue
                if not rows:
                    logger.debug(
                        "Consulta de índices '%s' vazia; tentando alternativa.",
                        label,
                    )
                    continue

                result = self._build_index_rows(
                    rows,
                    pk_set=pk_set,
                    prime_index_recid=prime_index_recid,
                    has_sequence=has_sequence,
                    index_recid_col=4 if include_index_recid else None,
                )
                if result:
                    logger.info(
                        "Índices carregados via consulta '%s' (%s linhas).",
                        label,
                        len(result),
                    )
                    return result

            if last_error is not None:
                logger.warning(
                    "Nenhuma consulta de índices retornou dados para a tabela: %s",
                    last_error,
                )
            return []
        except pyodbc.Error as exc:
            raise RuntimeError("Erro ao listar índices da tabela selecionada.") from exc
        finally:
            cursor.close()

    @staticmethod
    def _list_pk_fields(cursor: Cursor, recid_table: str) -> list[str]:
        """Return PK field names for the table."""
        try:
            cursor.execute(
                """
                SELECT
                    C."_Field-Name"
                FROM (
                    SELECT TOP 1
                        I.ROWID
                    FROM PUB."_Index" I
                    WHERE I."_file-recid" = ?
                        AND I."_Active" = 1
                        AND I."_Unique" = 1
                ) I
                    JOIN PUB."_Index-Field" IC
                        ON IC."_Index-recid" = I.ROWID
                    JOIN PUB."_field" C
                        ON C.ROWID = IC."_Field-recid"
                WITH (NOLOCK)
                """,
                recid_table,
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except pyodbc.Error as exc:
            raise RuntimeError("Erro ao listar campos de chave primaria.") from exc
