# Sample MCP Server

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server used
to smoke-test container deployments (e.g. on TrueFoundry).

It uses the `mcp` Python SDK (v2). By default it speaks MCP over the
**streamable-http** transport, so it runs as an ordinary long-lived HTTP
service inside a container. It can also run over **stdio** (set
`MCP_TRANSPORT=stdio`) for local MCP clients like Claude Desktop or Cursor
that spawn the server as a subprocess.

## What it exposes

- Tools: `add(a, b)`, `reverse_text(text)`, `get_server_time()`
- Resource: `info://server`
- MCP endpoint: `POST /mcp`
- Health check: `GET /health` -> `{"status": "ok", "time": <unix ts>}`

Configured via env vars:

| Var    | Default   | Purpose                          |
|--------|-----------|-----------------------------------|
| `HOST` | `0.0.0.0` | Bind address                            |
| `PORT` | `8000`    | Port the HTTP server listens on         |
| `MCP_TRANSPORT` | `streamable-http` | `streamable-http` or `stdio` |

## STDIO configuration (local MCP clients)

To register this server with an MCP client that talks stdio (Claude
Desktop, Cursor, etc.), point it at `server.py` with `MCP_TRANSPORT=stdio`.
See `mcp-stdio-config.json` for a ready-to-use snippet:

```json
{
  "mcpServers": {
    "sample-mcp-server": {
      "command": "python3",
      "args": ["/home/user/codePractice/mcp-server/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Merge this into your client's own config file (e.g.
`claude_desktop_config.json`) under its top-level `mcpServers` key, and
update the `args` path to wherever you checked this repo out. Make sure the
`mcp` package is installed for whatever Python the `command` resolves to
(activate the same venv, or use its absolute interpreter path instead of
`python3`).

## Run locally (no Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

Then check the health endpoint:

```bash
curl http://localhost:8000/health
```

And exercise the MCP handshake:

```bash
curl -N -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

Or point the [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
at it:

```bash
npx @modelcontextprotocol/inspector
# In the UI: transport = "Streamable HTTP", URL = http://localhost:8000/mcp
```

## Run with Docker

```bash
docker build -t sample-mcp-server .
docker run --rm -p 8000:8000 sample-mcp-server
curl http://localhost:8000/health
```

## Deploy to TrueFoundry

`truefoundry.yaml` in this folder is a ready-to-edit deployment spec. Its
`build_source` is set to `type: git`, so **TrueFoundry itself clones this
repo** (`repo_url` + `branch_name` in the file) and builds
`mcp-server/Dockerfile` server-side — you do not need a local checkout for
this to work. It exposes port `8000` and wires up `/health` as the
liveness/readiness probe.

1. Install the CLI and log in:
   ```bash
   pip install truefoundry
   tfy login
   ```
2. Edit `workspace_fqn: <your-workspace-fqn>` near the top of
   `mcp-server/truefoundry.yaml` to a real workspace (find one with
   `tfy get workspaces`, or in the UI under Workspaces — format is usually
   `<cluster>:<workspace-name>`). `tfy apply` reads the manifest as-is, so
   this field must already be set in the file; there's no `--workspace-fqn`
   flag for it like `tfy deploy` has.
3. Deploy (can be run from anywhere — the code comes from git, not disk):
   ```bash
   tfy apply -f mcp-server/truefoundry.yaml
   ```
4. Once deployed, TrueFoundry gives you a public/internal endpoint URL. Test
   it the same way as local:
   ```bash
   curl https://<your-service-endpoint>/health
   ```
   and point an MCP client's Streamable HTTP transport at
   `https://<your-service-endpoint>/mcp`.

Alternatively, skip the CLI and use the TrueFoundry UI: **New Service ->
Deploy from Git Repo**, paste this repo's URL, pick the `test-mcp-server`
branch, and set `mcp-server` as the subdirectory — it will detect the
`Dockerfile` there and prefill the same settings as `truefoundry.yaml`.

If you'd rather build from your local disk instead of git (e.g. to test
uncommitted changes), run `tfy deploy` from inside `mcp-server/` and change
`build_source` in the yaml to `type: local` (see the comment in the file).
