# Client Configuration Examples

Replace `/ABSOLUTE/PATH/...` with the real path on your machine.

## Codex

```toml
[mcp_servers.sqlite_lab]
command = "python3"
args = ["/ABSOLUTE/PATH/TO/implementation/mcp_server.py"]
```

## Claude Code

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "python3",
      "args": ["/ABSOLUTE/PATH/TO/implementation/mcp_server.py"],
      "env": {}
    }
  }
}
```

## Gemini CLI

```bash
gemini mcp add sqlite-lab /ABSOLUTE/PATH/TO/python3 /ABSOLUTE/PATH/TO/implementation/mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
```

## Suggested Demo Prompts

- `Use the sqlite_lab MCP server and show me all students in cohort A1.`
- `Use the sqlite_lab MCP server to insert a new student and confirm the inserted record.`
- `Use the sqlite_lab MCP server and compute the average student score by cohort.`
