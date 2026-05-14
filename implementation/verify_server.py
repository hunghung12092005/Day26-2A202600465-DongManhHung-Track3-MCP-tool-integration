from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from implementation.db import SQLiteAdapter, ValidationError
    from implementation.init_db import create_database
else:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import create_database


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    db_path = Path(create_database(base_dir / "verify_lab.db"))
    adapter = SQLiteAdapter(db_path)

    print("== SQLite MCP Lab Verification ==")
    print(f"Database path: {db_path}")
    print(f"Tables: {adapter.list_tables()}")

    print("\n1. Schema resource preview")
    print(adapter.database_schema_json())

    print("\n2. Valid search")
    search_result = adapter.search(
        table="students",
        filters=[{"column": "cohort", "operator": "eq", "value": "A1"}],
        order_by="score",
        descending=True,
        limit=5,
    )
    print(json.dumps(search_result, indent=2))

    print("\n3. Valid insert")
    insert_result = adapter.insert(
        table="students",
        values={
            "full_name": "Vo Khanh Linh",
            "cohort": "A1",
            "email": "linh.vo@example.com",
            "age": 19,
            "score": 8.9,
        },
    )
    print(json.dumps(insert_result, indent=2))

    print("\n4. Valid aggregate")
    aggregate_result = adapter.aggregate(
        table="students",
        metric="avg",
        column="score",
        group_by=["cohort"],
    )
    print(json.dumps(aggregate_result, indent=2))

    print("\n5. Invalid request demonstration")
    try:
        adapter.search(table="missing_table")
    except ValidationError as error:
        print({"ok": False, "error_type": "ValidationError", "message": str(error)})

    print("\nVerification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
