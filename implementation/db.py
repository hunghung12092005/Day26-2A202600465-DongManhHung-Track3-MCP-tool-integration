from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


SUPPORTED_OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "like": "LIKE",
    "in": "IN",
}

SUPPORTED_METRICS = {"count", "avg", "sum", "min", "max"}


class SQLiteAdapter:
    """SQLite access layer used by the MCP server and tests."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_tables(self) -> list[str]:
        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> dict[str, Any]:
        table_name = self._validate_table(table)
        with self.connect() as connection:
            rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {
            "table": table_name,
            "columns": [
                {
                    "cid": row["cid"],
                    "name": row["name"],
                    "type": row["type"],
                    "notnull": bool(row["notnull"]),
                    "default_value": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
                for row in rows
            ],
        }

    def get_database_schema(self) -> dict[str, Any]:
        return {
            "database": Path(self.db_path).name,
            "tables": [self.get_table_schema(table) for table in self.list_tables()],
        }

    def search(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: list[dict[str, Any]] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table_name = self._validate_table(table)
        schema = self.get_table_schema(table_name)
        allowed_columns = {column["name"] for column in schema["columns"]}
        selected = self._validate_selected_columns(columns, allowed_columns)
        where_sql, params = self._build_where_clause(filters or [], allowed_columns)
        order_sql = ""
        if order_by is not None:
            validated_order = self._validate_column(order_by, allowed_columns)
            direction = "DESC" if descending else "ASC"
            order_sql = f" ORDER BY {validated_order} {direction}"

        validated_limit = self._validate_non_negative_int(limit, "limit", minimum=1)
        validated_offset = self._validate_non_negative_int(offset, "offset", minimum=0)
        column_sql = ", ".join(selected)
        query = (
            f"SELECT {column_sql} FROM {table_name}"
            f"{where_sql}{order_sql} LIMIT ? OFFSET ?"
        )
        with self.connect() as connection:
            rows = connection.execute(query, [*params, validated_limit, validated_offset]).fetchall()
        return {
            "table": table_name,
            "columns": selected,
            "limit": validated_limit,
            "offset": validated_offset,
            "row_count": len(rows),
            "rows": [dict(row) for row in rows],
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table_name = self._validate_table(table)
        if not values:
            raise ValidationError("Insert payload must not be empty.")

        schema = self.get_table_schema(table_name)
        allowed_columns = {column["name"] for column in schema["columns"]}
        columns = [self._validate_column(column, allowed_columns) for column in values]
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        query = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"
        payload = [values[column] for column in columns]
        with self.connect() as connection:
            cursor = connection.execute(query, payload)
            connection.commit()
            row_id = cursor.lastrowid
            created = connection.execute(
                f"SELECT * FROM {table_name} WHERE rowid = ?",
                [row_id],
            ).fetchone()
        return {
            "table": table_name,
            "inserted_id": row_id,
            "values": dict(created) if created is not None else values,
        }

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[dict[str, Any]] | None = None,
        group_by: list[str] | None = None,
    ) -> dict[str, Any]:
        table_name = self._validate_table(table)
        normalized_metric = metric.lower().strip()
        if normalized_metric not in SUPPORTED_METRICS:
            raise ValidationError(
                f"Unsupported metric '{metric}'. Supported metrics: {sorted(SUPPORTED_METRICS)}"
            )

        schema = self.get_table_schema(table_name)
        allowed_columns = {column_info["name"] for column_info in schema["columns"]}
        where_sql, params = self._build_where_clause(filters or [], allowed_columns)

        if normalized_metric == "count":
            metric_sql = "COUNT(*)"
        else:
            if column is None:
                raise ValidationError(f"Metric '{normalized_metric}' requires a column name.")
            validated_column = self._validate_column(column, allowed_columns)
            metric_sql = f"{normalized_metric.upper()}({validated_column})"

        group_columns: list[str] = []
        if group_by:
            group_columns = [self._validate_column(item, allowed_columns) for item in group_by]
            select_sql = ", ".join([*group_columns, f"{metric_sql} AS value"])
            group_sql = f" GROUP BY {', '.join(group_columns)}"
        else:
            select_sql = f"{metric_sql} AS value"
            group_sql = ""

        query = f"SELECT {select_sql} FROM {table_name}{where_sql}{group_sql}"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return {
            "table": table_name,
            "metric": normalized_metric,
            "column": column,
            "group_by": group_columns,
            "row_count": len(rows),
            "rows": [dict(row) for row in rows],
        }

    def database_schema_json(self) -> str:
        return json.dumps(self.get_database_schema(), indent=2)

    def table_schema_json(self, table: str) -> str:
        return json.dumps(self.get_table_schema(table), indent=2)

    def _validate_table(self, table: str) -> str:
        self._validate_identifier_type(table, "table")
        if table not in self.list_tables():
            raise ValidationError(f"Unknown table '{table}'.")
        return table

    def _validate_column(self, column: str, allowed_columns: set[str]) -> str:
        self._validate_identifier_type(column, "column")
        if column not in allowed_columns:
            raise ValidationError(f"Unknown column '{column}'.")
        return column

    def _validate_selected_columns(
        self, columns: list[str] | None, allowed_columns: set[str]
    ) -> list[str]:
        if columns is None:
            return sorted(allowed_columns)
        if not columns:
            raise ValidationError("If provided, columns must not be empty.")
        return [self._validate_column(column, allowed_columns) for column in columns]

    def _validate_identifier_type(self, value: Any, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label.title()} name must be a non-empty string.")

    def _validate_non_negative_int(
        self, value: Any, label: str, minimum: int
    ) -> int:
        if not isinstance(value, int):
            raise ValidationError(f"{label.title()} must be an integer.")
        if value < minimum:
            raise ValidationError(f"{label.title()} must be >= {minimum}.")
        return value

    def _build_where_clause(
        self, filters: list[dict[str, Any]], allowed_columns: set[str]
    ) -> tuple[str, list[Any]]:
        if not filters:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for item in filters:
            if not isinstance(item, dict):
                raise ValidationError("Each filter must be an object.")
            column = self._validate_column(item.get("column"), allowed_columns)
            operator = item.get("operator", "eq")
            if operator not in SUPPORTED_OPERATORS:
                raise ValidationError(
                    f"Unsupported operator '{operator}'. Supported operators: {sorted(SUPPORTED_OPERATORS)}"
                )
            value = item.get("value")
            sql_operator = SUPPORTED_OPERATORS[operator]
            if operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError("Operator 'in' requires a non-empty list value.")
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{column} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{column} {sql_operator} ?")
                params.append(value)
        return f" WHERE {' AND '.join(clauses)}", params
