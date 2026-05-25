"""Generate SQL helper scripts from TOTVS metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from totvs_helper.services.constants import FREE_FIELDS_TO_IGNORE


@dataclass(frozen=True)
class GeneratedScripts:
    query_etl: str
    ddl_create: str
    script_delete: str
    script_update: str
    differential: str

    @property
    def diferencial(self) -> str:
        """Backward-compatible alias kept for existing callers."""
        return self.differential


class ScriptGenerator:
    """Service responsible for SQL and SSIS snippets generation."""

    def generate_helpers(
        self,
        include_free_fields: bool,
        multi_company: bool,
        selected_table: str,
        fields: Iterable[Sequence],
        pk_fields: list[str],
    ) -> GeneratedScripts:
        filtered_fields = [
            field
            for field in fields
            if include_free_fields or field[0] not in FREE_FIELDS_TO_IGNORE
        ]
        table_formatted = selected_table.title().replace("-", "")

        include_base = not multi_company
        query_etl = self._build_etl_query(
            selected_table, filtered_fields, multi_company, include_base=include_base
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
        fields: list[Sequence],
        multi_company: bool,
        *,
        include_base: bool = False,
    ) -> str:
        projections: List[str] = []
        if multi_company:
            projections.append("    '' as \"empresa\"")
        elif include_base:
            projections.append("    '' as \"BASE\"")

        for field in fields:
            projections.append(self._map_etl_projection(field))

        query_body = ", \n".join(projections)
        return f'SELECT \n{query_body}\nfrom PUB."{selected_table}" WITH (NOLOCK)'

    def _build_ddl(
        self,
        table_formatted: str,
        fields: list[Sequence],
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
            field_name = field[0]
            width = field[2]
            decimals = field[3]
            fetch_datatype = field[4]
            sql_type = self._map_sql_type(fetch_datatype, width, decimals)
            ddl_lines.append(f"    [{field_name}] {sql_type},")

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
        fields: list[Sequence],
        pk_fields: list[str],
    ) -> tuple[str, str]:
        assignments: List[str] = []
        differential_parts: List[str] = []

        for field in fields:
            field_name = field[0]
            if field_name in pk_fields:
                continue

            fetch_datatype = field[4]
            assignments.append(f"[{field_name}] = ?")
            replacement = self._replacement_for_differential(fetch_datatype)
            differential_parts.append(
                "REPLACENULL([{0}],{1}) != REPLACENULL([{0}_LKP],{1})".format(
                    field_name, replacement
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
    def _map_etl_projection(field: Sequence) -> str:
        field_name = field[0]
        data_type = field[1]
        width = field[2]

        if data_type == "character":
            return f'    SUBSTRING("{field_name}",1,{width}) AS "{field_name}"'
        if data_type == "date":
            return (
                "    case \n"
                f"        when \"{field_name}\" <= '01/01/1900' "
                "then convert('date', '01/01/1900') \n"
                f"        when \"{field_name}\" >= '12/31/9999' "
                "then convert('date', '12/31/9999') \n"
                f"        else convert('date', \"{field_name}\") \n"
                f'    end AS "{field_name}"'
            )
        if data_type == "logical":
            return (
                "    CONVERT('bit', CASE WHEN \"{0}\" <> '1' THEN '0' "
                "ELSE '1' END) AS \"{0}\""
            ).format(field_name)
        return f'    "{field_name}"'

    @staticmethod
    def _replacement_for_differential(fetch_datatype: str) -> str:
        if fetch_datatype in ("numeric", "decimal", "integer"):
            return "0"
        if fetch_datatype in ("timestamp", "datetime", "date"):
            return '(DT_DBDATE)"1950-01-01"'
        return '""'
