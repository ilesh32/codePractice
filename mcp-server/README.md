# Sample MCP Server

A minimal [Model Context Protocol](https://modelcontextprotocol.io) server used
to smoke-test container deployments (e.g. on TrueFoundry).

It uses the `mcp` Python SDK (v2) and speaks MCP over the **streamable-http**
transport, so it runs as an ordinary long-lived HTTP service inside a
container rather than needing a stdio-attached client.

## What it exposes

- Tools: `add(a, b)`, `reverse_text(text)`, `get_server_time()`
- Resource: `info://server`
- MCP endpoint: `POST /mcp`
- Health check: `GET /health` -> `{"status": "ok", "time": <unix ts>}`

Configured via env vars:

| Var    | Default   | Purpose                          |
|--------|-----------|-----------------------------------|
| `HOST` | `0.0.0.0` | Bind address                      |
| `PORT` | `8000`    | Port the HTTP server listens on   |

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

`truefoundry.yaml` in this folder is a ready-to-edit deployment spec that
builds the image from the `Dockerfile`, exposes port `8000`, and wires up the
`/health` endpoint as the liveness/readiness probe.

1. Install the CLI and log in:
   ```bash
   pip install truefoundry
   tfy login
   ```
2. Deploy:
   ```bash
   tfy deploy --file truefoundry.yaml --workspace-fqn <your-workspace-fqn>
   ```
   (replace `<your-workspace-fqn>` with the workspace you want to deploy
   into — find it in the TrueFoundry UI under Workspaces).
3. Once deployed, TrueFoundry gives you a public/internal endpoint URL. Test
   it the same way as local:
   ```bash
   curl https://<your-service-endpoint>/health
   ```
   and point an MCP client's Streamable HTTP transport at
   `https://<your-service-endpoint>/mcp`.

Alternatively, skip the CLI and create the Service from the TrueFoundry UI by
pointing it at this repo — it will detect the `Dockerfile` and let you set
the port/env vars/probes interactively (matching what's in `truefoundry.yaml`).
