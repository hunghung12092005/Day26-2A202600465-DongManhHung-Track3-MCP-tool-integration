# Lab 26: Database MCP Server with FastMCP and SQLite

This project implements a local MCP server that exposes a SQLite database through three required tools:

- `search`
- `insert`
- `aggregate`

It also exposes database schema context through MCP resources:

- `schema://database`
- `schema://table/{table_name}`

The implementation is organized so the database layer is isolated from the MCP layer, making it easy to test and easier to swap the backend later.

## 1. Project Structure

```text
.
├── AGENTS.md
├── docs/
│   └── client-config-examples.md
├── implementation/
│   ├── __init__.py
│   ├── db.py
│   ├── init_db.py
│   ├── mcp_server.py
│   ├── start_inspector.sh
│   ├── verify_server.py
│   └── tests/
│       └── test_server.py
├── pseudocode/
├── requirements.txt
├── Rubric.md
└── Tips.md
```

## 2. Features Implemented

### MCP Tools

1. `search`
   - validates table names and selected columns
   - supports filters with operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `in`
   - supports ordering
   - supports pagination with `limit` and `offset`

2. `insert`
   - validates target table and columns
   - rejects empty payloads
   - uses parameterized SQL
   - returns the inserted row

3. `aggregate`
   - supports `count`, `avg`, `sum`, `min`, `max`
   - validates metric, table, column, and group-by fields
   - supports optional filters and grouping

### MCP Resources

- `schema://database`
  - returns the full schema as JSON text
- `schema://table/{table_name}`
  - returns a single validated table schema as JSON text

### Safety and Validation

- unknown tables are rejected
- unknown columns are rejected
- unsupported operators are rejected
- invalid aggregate requests are rejected
- empty inserts are rejected
- SQL statements use placeholders for runtime values

## 3. Database Model

The seeded demo database includes:

- `students`
- `courses`
- `enrollments`

This dataset supports all required demo scenarios:

- search all students in cohort `A1`
- insert a new student
- count rows in a table
- compute average score by cohort
- read the full schema resource
- read `schema://table/students`
- show invalid requests safely

## 4. Setup Instructions

### Prerequisites

- Python 3.10+
- `pip`
- optional: Node.js for MCP Inspector

### Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Initialize the SQLite database

```bash
python3 implementation/init_db.py
```

Expected result:

- a file named `implementation/sqlite_lab.db` is created
- demo data is loaded into the three tables

## 5. Running the MCP Server

Start the server over stdio:

```bash
python3 implementation/mcp_server.py
```

The server creates the SQLite database automatically if it does not exist.

Optional environment variable:

```bash
SQLITE_LAB_DB_PATH=/custom/path/lab.db python3 implementation/mcp_server.py
```

## 6. Tool Contracts

### `search`

Example request shape:

```json
{
  "table": "students",
  "filters": [
    { "column": "cohort", "operator": "eq", "value": "A1" }
  ],
  "columns": ["full_name", "score"],
  "limit": 10,
  "offset": 0,
  "order_by": "score",
  "descending": true
}
```

Example response shape:

```json
{
  "ok": true,
  "table": "students",
  "columns": ["full_name", "score"],
  "limit": 10,
  "offset": 0,
  "row_count": 2,
  "rows": [
    { "full_name": "Nguyen Van An", "score": 8.6 },
    { "full_name": "Tran Minh Chau", "score": 7.9 }
  ]
}
```

### `insert`

Example request shape:

```json
{
  "table": "students",
  "values": {
    "full_name": "Vo Khanh Linh",
    "cohort": "A1",
    "email": "linh.vo@example.com",
    "age": 19,
    "score": 8.9
  }
}
```

### `aggregate`

Example request shape:

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": ["cohort"]
}
```

## 7. Resource Usage

- `schema://database`
- `schema://table/students`
- `schema://table/courses`

These resources return JSON text suitable for MCP-aware clients and inspectors.

## 8. Verification Steps

### Run automated tests

```bash
python3 -m pytest implementation/tests/test_server.py
```

Covered checks:

- table discovery
- valid search flow
- valid insert flow
- valid aggregate flow
- database schema serialization
- rejection of invalid tables
- rejection of invalid columns
- rejection of unsupported operators
- rejection of empty inserts

### Run repeatable verification script

```bash
python3 implementation/verify_server.py
```

This script demonstrates:

1. database initialization
2. schema output
3. valid `search`
4. valid `insert`
5. valid `aggregate`
6. invalid request handling

### Run MCP Inspector

```bash
chmod +x implementation/start_inspector.sh
./implementation/start_inspector.sh
```

Inspector checklist:

- confirm the server starts
- confirm `search`, `insert`, and `aggregate` are discoverable
- confirm resources are discoverable
- run a valid call
- run an invalid call and verify the error is clear

## 9. Client Configuration Example

See the detailed file here:

- [docs/client-config-examples.md](/home/hung/code/AI_CODE_VIN/lab/Day26/Day26-2A202600465-DongManhHung-Track3-MCP-tool-integration/docs/client-config-examples.md)

Quick Codex example:

```toml
[mcp_servers.sqlite_lab]
command = "python3"
args = ["/ABSOLUTE/PATH/TO/implementation/mcp_server.py"]
```

Suggested `AGENTS.md` instruction is already included in this repository.

## 10. Demo Script for a 2-Minute Video

Use this order:

1. Show the repository structure.
2. Run `python3 implementation/init_db.py`.
3. Run `python3 -m pytest implementation/tests/test_server.py`.
4. Launch MCP Inspector.
5. Show the three tools in Inspector.
6. Run `search` for students in cohort `A1`.
7. Run `insert` for one new student.
8. Run `aggregate` for average score by cohort.
9. Open `schema://database`.
10. Open `schema://table/students`.
11. Show one invalid request such as table `missing_table`.

## 11. Known Environment Note

In the current local environment used to build this submission, `fastmcp` was not preinstalled. The repository includes the correct implementation and dependency declaration in `requirements.txt`, but you must install dependencies before starting the actual MCP server or using Inspector.

## 12. Rubric Coverage Summary

- Server foundation: implemented
- Required tools: implemented
- MCP resources: implemented
- Safety and validation: implemented
- Verification story: implemented with tests and verify script
- Client integration: documented with config examples and demo flow
