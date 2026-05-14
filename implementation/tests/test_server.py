from __future__ import annotations

import json
from pathlib import Path

import pytest

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import create_database


@pytest.fixture()
def adapter(tmp_path: Path) -> SQLiteAdapter:
    db_path = tmp_path / "test_lab.db"
    create_database(db_path)
    return SQLiteAdapter(db_path)


def test_list_tables(adapter: SQLiteAdapter) -> None:
    assert adapter.list_tables() == ["courses", "enrollments", "students"]


def test_search_with_filters_ordering_and_pagination(adapter: SQLiteAdapter) -> None:
    result = adapter.search(
        table="students",
        filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
        columns=["full_name", "score"],
        order_by="score",
        descending=True,
        limit=1,
        offset=0,
    )
    assert result["row_count"] == 1
    assert result["rows"][0]["full_name"] == "Nguyen Van An"


def test_insert_returns_inserted_payload(adapter: SQLiteAdapter) -> None:
    result = adapter.insert(
        table="students",
        values={
            "full_name": "Bui Gia Bao",
            "cohort": "C3",
            "email": "bao.bui@example.com",
            "age": 20,
            "score": 7.7,
        },
    )
    assert result["values"]["email"] == "bao.bui@example.com"
    assert result["inserted_id"] > 0


def test_aggregate_avg_group_by(adapter: SQLiteAdapter) -> None:
    result = adapter.aggregate(
        table="students",
        metric="avg",
        column="score",
        group_by=["cohort"],
    )
    assert result["row_count"] == 3
    assert {row["cohort"] for row in result["rows"]} == {"A1", "B2", "C3"}


def test_database_schema_resource_shape(adapter: SQLiteAdapter) -> None:
    resource = json.loads(adapter.database_schema_json())
    assert resource["database"].endswith(".db")
    assert len(resource["tables"]) == 3


def test_invalid_table_is_rejected(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unknown table"):
        adapter.search(table="hackers")


def test_invalid_column_is_rejected(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unknown column"):
        adapter.search(table="students", columns=["password"])


def test_unsupported_operator_is_rejected(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="Unsupported operator"):
        adapter.search(
            table="students",
            filters=[{"column": "score", "operator": "between", "value": [1, 2]}],
        )


def test_empty_insert_is_rejected(adapter: SQLiteAdapter) -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        adapter.insert(table="students", values={})
