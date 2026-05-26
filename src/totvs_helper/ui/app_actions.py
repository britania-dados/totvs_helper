"""Business flows for Totvs Helper (no Tk dependencies)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from totvs_helper.errors import OdbcConnectionError, TotvsHelperError
from totvs_helper.infra.odbc_client import FieldMeta, OdbcClient
from totvs_helper.services.pentaho import PentahoExporter
from totvs_helper.services.pentaho.constants import (
    DEFAULT_INCLUDE_FREE_FIELDS,
    is_multi_company_dsn,
)
from totvs_helper.services.script_generator import GeneratedScripts, ScriptGenerator
from totvs_helper.ui.state import SessionState


class AppActions:
    """ODBC, script generation, and Pentaho export orchestration."""

    def __init__(
        self,
        odbc: OdbcClient,
        generator: ScriptGenerator,
        pentaho: PentahoExporter,
        state: SessionState,
    ) -> None:
        self._odbc = odbc
        self._generator = generator
        self._pentaho = pentaho
        self._state = state

    def list_dsns(self) -> List[str]:
        return self._odbc.list_odbcs()

    def test_connection(self, dsn: str) -> None:
        self._odbc.test_connection(dsn)

    def connect(self, dsn: str) -> tuple[object, List[str]]:
        connection = self._odbc.connect(dsn)
        tables = self._odbc.list_tables(connection)
        return connection, tables

    def apply_dsn_option_defaults(self, dsn: str) -> None:
        self._state.include_free_fields = DEFAULT_INCLUDE_FREE_FIELDS
        self._state.multi_company = is_multi_company_dsn(dsn)

    def load_table_preview(
        self,
        table: str,
        *,
        offset: int,
        cached_fields: Optional[List[FieldMeta]] = None,
    ) -> Dict[str, Any]:
        connection = self._state.connection
        if connection is None:
            raise OdbcConnectionError("Sem conexão ODBC ativa.")

        index_rows: list = []
        if offset == 0:
            recid = self._odbc.get_table_recid(table)
            fields, pk_fields = self._odbc.list_fields_and_pk(recid, connection)
            index_rows = self._odbc.list_table_indexes(recid, connection, pk_fields)
        else:
            if cached_fields:
                fields = list(cached_fields)
                pk_fields: list[str] = []
            else:
                recid = self._odbc.get_table_recid(table)
                fields, pk_fields = self._odbc.list_fields_and_pk(recid, connection)
        sample_columns: Optional[List[str]] = None
        sample_rows: Optional[list] = None
        sample_error: Optional[str] = None
        try:
            sample_columns, sample_rows = self._odbc.fetch_sample_rows(
                table,
                fields,
                connection,
                pk_fields=pk_fields,
                offset=offset,
            )
        except RuntimeError as exc:
            sample_error = str(exc)
        return {
            "fields": fields,
            "pk_fields": pk_fields,
            "index_rows": index_rows,
            "sample_columns": sample_columns,
            "sample_rows": sample_rows,
            "sample_error": sample_error,
        }

    def generate_scripts(
        self,
        table: str,
        fields: List[FieldMeta],
        pk_fields: List[str],
    ) -> GeneratedScripts:
        return self._generator.generate_helpers(
            include_free_fields=self._state.include_free_fields,
            multi_company=self._state.multi_company,
            selected_table=table,
            fields=fields,
            pk_fields=list(pk_fields),
            ecom_keys=self._state.ecom_keys,
        )

    def resolve_fields_for_table(
        self, table: str, cached_fields: List[FieldMeta]
    ) -> tuple[List[FieldMeta], List[str]]:
        if cached_fields:
            return list(cached_fields), []
        connection = self._state.connection
        if connection is None:
            raise OdbcConnectionError("Sem conexão ODBC ativa.")
        recid = self._odbc.get_table_recid(table)
        fields, pk_fields = self._odbc.list_fields_and_pk(recid, connection)
        return list(fields), pk_fields

    def generate_pentaho(
        self,
        output_dir: Path,
        table: str,
        dsn: str,
        fields: List[FieldMeta],
        pk_fields: List[str],
    ) -> Path:
        if fields:
            use_fields = list(fields)
            use_pk = list(pk_fields)
        else:
            use_fields, use_pk = self.resolve_fields_for_table(table, [])
        if not use_fields:
            raise TotvsHelperError(
                "Metadados da tabela indisponíveis para gerar a carga."
            )
        result = self._pentaho.generate(
            output_dir,
            progress_table=table,
            dsn=dsn,
            fields=use_fields,
            pk_fields=use_pk,
            include_free_fields=self._state.include_free_fields,
            multi_company=self._state.multi_company,
        )
        return result.job_path
