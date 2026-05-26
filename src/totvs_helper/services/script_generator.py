"""Generate SQL helper scripts from TOTVS metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from totvs_helper.infra.odbc_client import FieldMeta
from totvs_helper.services.constants import filter_fields
from totvs_helper.services.ecom_emitente_keys import map_ecom_emitente_etl_projection


@dataclass(frozen=True)
class GeneratedScripts:
    query_etl: str
    ddl_create: str
    script_delete: str
    script_update: str
    differential: str


class ScriptGenerator:
    """Service responsible for SQL and SSIS snippets generation."""

    def generate_helpers(
        self,
        include_free_fields: bool,
        multi_company: bool,
        selected_table: str,
        fields: Iterable[FieldMeta],
        pk_fields: list[str],
        *,
        ecom_keys: bool = False,
    ) -> GeneratedScripts:
        filtered_fields = filter_fields(fields, include_free_fields)
        table_formatted = selected_table.title().replace("-", "")

        include_base = not multi_company
        query_etl = self._build_etl_query(
            selected_table,
            filtered_fields,
            multi_company,
            include_base=include_base,
            ecom_keys=ecom_keys,
        )
        update_assignments, differential = self._build_update_parts(
            filtered_fields, pk_fields
        )
        where_clause = self._build_where_clause(
            pk_fields, multi_company, include_base=include_base
        )
        ddl_create = self._build_ddl(
            table_formatted,
            filtered_fields,
            pk_fields,
            multi_company,
            include_base=include_base,
        )
        script_update = self._build_update_statement(
            table_formatted, update_assignments, where_clause
        )
        script_delete = self._build_delete_statement(table_formatted, where_clause)

        return GeneratedScripts(
            query_etl=query_etl,
            ddl_create=ddl_create,
            script_delete=script_delete,
            script_update=script_update,
            differential=differential,
        )

    def _build_etl_query(
        self,
        selected_table: str,
        fields: list[FieldMeta],
        multi_company: bool,
        *,
        include_base: bool = False,
        ecom_keys: bool = False,
    ) -> str:
        projections: List[str] = []
        if multi_company:
            projections.append("    '' as \"empresa\"")
        elif include_base:
            projections.append("    '' as \"BASE\"")

        for field in fields:
            ecom_line = map_ecom_emitente_etl_projection(
                field, progress_table=selected_table, ecom_keys=ecom_keys
            )
            if ecom_line is not None:
                projections.append(ecom_line)
            else:
                projections.append(self._map_etl_projection(field))

        query_body = ", \n".join(projections)
        return f'SELECT \n{query_body}\nfrom PUB."{selected_table}" WITH (NOLOCK)'

    def _build_ddl(
        self,
        table_formatted: str,
        fields: list[FieldMeta],
        pk_fields: list[str],
        multi_company: bool,
        *,
        include_base: bool = False,
    ) -> str:
        ddl_lines = [f"CREATE TABLE [tot].[{table_formatted}] ("]
        if multi_company:
            ddl_lines.append("    [empresa] [varchar](2),")
        elif include_base:
            ddl_lines.append("    [BASE] [varchar](8),")

        for field in fields:
            sql_type = self._map_sql_type(
                field.fetch_datatype, field.width, field.decimals
            )
            ddl_lines.append(f"    [{field.name}] {sql_type},")

        ddl_lines.append("    [DATA_ALTERACAO] [datetime2](7) DEFAULT(GETDATE()),")
        ddl_lines.append("PRIMARY KEY (")

        for field in pk_fields:
            ddl_lines.append(f"    [{field}],")

        if multi_company:
            ddl_lines.append("    [empresa] ")
        elif include_base:
            ddl_lines.append("    [BASE] ")
        else:
            last_pk = ddl_lines.pop()
            ddl_lines.append(last_pk.rstrip(","))

        ddl_lines.append("))")
        return "\n".join(ddl_lines)

    def _build_update_parts(
        self,
        fields: list[FieldMeta],
        pk_fields: list[str],
    ) -> tuple[str, str]:
        assignments: List[str] = []
        differential_parts: List[str] = []

        for field in fields:
            if field.name in pk_fields:
                continue

            assignments.append(f"[{field.name}] = ?")
            replacement = self._replacement_for_differential(field.fetch_datatype)
            differential_parts.append(
                "REPLACENULL([{0}],{1}) != REPLACENULL([{0}_LKP],{1})".format(
                    field.name, replacement
                )
            )

        update_assignments = "\n        ,".join(assignments)
        differential = " || ".join(differential_parts)
        return update_assignments, differential

    @staticmethod
    def _build_where_clause(
        pk_fields: list[str], multi_company: bool, *, include_base: bool = False
    ) -> str:
        where_lines = [f"[{field}] = ?" for field in pk_fields]
        if multi_company:
            where_lines.append("[empresa] = ?")
        elif include_base:
            where_lines.append("[BASE] = ?")
        return "\n    AND ".join(where_lines)

    @staticmethod
    def _build_update_statement(
        table_formatted: str,
        update_assignments: str,
        where_clause: str,
    ) -> str:
        return (
            "UPDATE A \n"
            "    SET "
            f"{update_assignments} \n"
            "    ,[DATA_ALTERACAO] = GETDATE() \n"
            f"FROM tot.[{table_formatted}] A WITH(NOLOCK) \n"
            f"WHERE {where_clause}"
        )

    @staticmethod
    def _build_delete_statement(table_formatted: str, where_clause: str) -> str:
        return (
            "DELETE A\n"
            f"FROM tot.[{table_formatted}] A WITH(NOLOCK) \n"
            f"WHERE {where_clause}"
        )

    @staticmethod
    def _map_sql_type(fetch_datatype: str, width: int, decimals: int) -> str:
        if fetch_datatype == "varchar":
            return f"[varchar]({width})"
        if fetch_datatype in ("numeric", "decimal"):
            return f"[numeric]({width},{decimals})"
        if fetch_datatype in ("datetime", "timestamp"):
            return "[datetime2](7)"
        if fetch_datatype in ("lvarbinary", "varbinary", "blob"):
            return "[varbinary](max)"
        return f"[{fetch_datatype}]"

    @staticmethod
    def _map_etl_projection(field: FieldMeta) -> str:
        if field.data_type == "character":
            return (
                f'    SUBSTRING("{field.name}",1,{field.width}) AS "{field.name}"'
            )
        if field.data_type == "date":
            return (
                "    case \n"
                f"        when \"{field.name}\" <= '01/01/1900' "
                "then convert('date', '01/01/1900') \n"
                f"        when \"{field.name}\" >= '12/31/9999' "
                "then convert('date', '12/31/9999') \n"
                f"        else convert('date', \"{field.name}\") \n"
                f'    end AS "{field.name}"'
            )
        if field.data_type == "logical":
            return (
                "    CONVERT('bit', CASE WHEN \"{0}\" <> '1' THEN '0' "
                "ELSE '1' END) AS \"{0}\""
            ).format(field.name)
        return f'    "{field.name}"'

    @staticmethod
    def _replacement_for_differential(fetch_datatype: str) -> str:
        if fetch_datatype in ("numeric", "decimal", "integer"):
            return "0"
        if fetch_datatype in ("timestamp", "datetime", "date"):
            return '(DT_DBDATE)"1950-01-01"'
        return '""'
