from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from implementation.db import SQLiteAdapter, ValidationError
    from implementation.init_db import DEFAULT_DB_PATH, create_database
else:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import DEFAULT_DB_PATH, create_database

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise ImportError(
        "fastmcp is not installed. Run `pip install -r requirements.txt` before starting the server."
    ) from exc


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("SQLITE_LAB_DB_PATH", DEFAULT_DB_PATH))

if not DB_PATH.exists():
    create_database(DB_PATH)

adapter = SQLiteAdapter(DB_PATH)
mcp = FastMCP("SQLite Lab MCP Server")


def _tool_error(error: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": error.__class__.__name__,
        "message": str(error),
    }


@mcp.tool(name="search")
def search(
    table: str,
    filters: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search a table with filters, ordering, and pagination."""
    try:
        result = adapter.search(
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
    except (ValidationError, ValueError, TypeError) as error:
        return _tool_error(error)
    return {"ok": True, **result}


@mcp.tool(name="insert")
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert a row into a validated table and return the inserted payload."""
    try:
        result = adapter.insert(table=table, values=values)
    except (ValidationError, ValueError, TypeError) as error:
        return _tool_error(error)
    return {"ok": True, **result}


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    group_by: list[str] | None = None,
) -> dict[str, Any]:
    """Aggregate rows using count, avg, sum, min, or max."""
    try:
        result = adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
    except (ValidationError, ValueError, TypeError) as error:
        return _tool_error(error)
    return {"ok": True, **result}


@mcp.resource("schema://database")
def database_schema() -> str:
    """Return the full database schema as JSON text."""
    return adapter.database_schema_json()


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """Return the schema for a single validated table."""
    try:
        return adapter.table_schema_json(table_name)
    except ValidationError as error:
        return json.dumps(_tool_error(error), indent=2)


if __name__ == "__main__":
    mcp.run()
