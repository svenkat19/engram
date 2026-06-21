# Getting Started with Engram

Engram is a local memory server for AI-assisted software engineering. It gives your
AI coding tools — Claude Code, Cursor, Copilot, or anything that speaks REST or
MCP — a shared, persistent knowledge layer backed by SQLite.

Instead of each tool building its own fragmented context, engram stores architecture
decisions, bug history, failed attempts, and design rationale in one place. It
indexes everything with hybrid search (full-text + semantic vectors) so your tools
can recall relevant context automatically.

This guide walks you through installation, first use, and connecting engram to your
AI tools.

## Prerequisites

- Python 3.11 or later
- pip (or uv)
- Git (for `engram ingest git`)

No external databases, Docker, or cloud services required — everything runs locally
in SQLite.

## Install

Clone the repository and install in development mode:

```bash
git clone https://github.com/shvenkat/engram.git
cd engram
pip install -e ".[dev]"
```

This installs the `engram` CLI and all dependencies, including a local embedding
model (~80 MB download on first run).

Verify the install:

```bash
engram --help
```

## Start the server

```bash
engram server start
```

This starts the REST API on `http://127.0.0.1:8741`. The database is created
automatically at `~/.engram/engram.db`.

Check that it's running:

```bash
curl http://localhost:8741/api/v1/admin/health
```

You should see `{"status": "ok"}`.

## Store your first memory

### From the CLI

Record an architecture decision:

```bash
engram add decision "Use SQLite for storage" \
  --project my-project \
  --tags architecture,storage
```

Add a quick note:

```bash
engram add note "Auth service uses JWT with 15-minute expiry" \
  --project my-project \
  --tags auth,security
```

Record something that didn't work (so nobody tries it again):

```bash
engram add failed-attempt "Tried Redis for session storage" \
  --why "Added operational complexity without meaningful latency improvement" \
  --lessons "SQLite WAL mode handles our concurrency needs"
```

### From the REST API

```bash
curl -X POST http://localhost:8741/api/v1/entities \
  -H 'Content-Type: application/json' \
  -d '{
    "entity_type": "decision",
    "title": "Use SQLite for storage",
    "content": "Local-first, zero-dependency storage with sqlite-vec for vector search.",
    "project": "my-project",
    "tags": ["architecture", "storage"]
  }'
```

## Search your memories

Engram combines full-text search (SQLite FTS5) with semantic vector search
(sqlite-vec) using Reciprocal Rank Fusion, so you can search by keyword or meaning.

```bash
engram search "database architecture"
```

Filter by type and project:

```bash
engram search "authentication" --type decision --project my-project --limit 5
```

Or via the API:

```bash
curl -X POST http://localhost:8741/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "storage architecture", "limit": 10}'
```

## Connect to Claude Code

Add engram to your MCP configuration so Claude Code can remember and recall
context automatically.

Add to `~/.claude.json` (or your project's `.claude/settings.json`):

```json
{
  "mcpServers": {
    "engram": {
      "command": "python",
      "args": ["-m", "engram.mcp_server.server"]
    }
  }
}
```

Restart Claude Code. You now have 10 MCP tools available:

| Tool | What it does |
|------|-------------|
| `remember` | Store any knowledge — decisions, bugs, snippets, context |
| `recall` | Semantic search across all memories |
| `recall_about_file` | Find everything known about a specific file |
| `record_decision` | Record an architecture/design decision (ADR-style) |
| `record_failed_attempt` | Record what didn't work and why |
| `get_context` | Session-start bundle: recent decisions, active bugs, file knowledge |
| `get_entity_history` | Full audit trail for an entity |
| `link_entities` | Create relationships in the knowledge graph |
| `find_contradictions` | Surface conflicting or superseded knowledge |
| `run_quality_check` | Recompute importance scores, apply decay, archive stale items |

### Suggested workflow with Claude Code

At the start of a session, Claude can call `get_context` with the files you're
working on to pull in relevant decisions, known bugs, and prior context.

As you work, it can `remember` new knowledge and `record_decision` when you make
architectural choices. If something doesn't work out, `record_failed_attempt` saves
the context so the next session (or the next developer) doesn't repeat the mistake.

## Connect to Cursor

Add to your project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "engram": {
      "command": "python",
      "args": ["-m", "engram.mcp_server.server"]
    }
  }
}
```

Any MCP-compatible tool can connect the same way — only the config file location
differs.

## Ingest existing knowledge

Pull commit history from a git repository into engram:

```bash
curl -X POST http://localhost:8741/api/v1/ingest/git \
  -H 'Content-Type: application/json' \
  -d '{"repo_path": "/path/to/your/repo", "project": "my-project"}'
```

Ingest markdown documentation:

```bash
curl -X POST http://localhost:8741/api/v1/ingest/markdown \
  -H 'Content-Type: application/json' \
  -d '{"path": "/path/to/docs", "project": "my-project"}'
```

## Use the dashboard

Build and open the web dashboard:

```bash
make dashboard
engram server start
```

Then open `http://localhost:8741` in your browser. The dashboard provides:

- **Search** — interactive search with filters and result previews
- **Graph** — D3-force visualization of the knowledge graph
- **Entity detail** — full content, provenance history, and relationships

## View entity details

Inspect a specific entity and its audit trail:

```bash
engram show <entity-id>
engram show <entity-id> --provenance
```

## Admin commands

Check storage stats:

```bash
engram admin stats
```

Rebuild search indexes (after a schema migration or if search seems off):

```bash
engram admin reindex
```

## Configuration

All settings use environment variables with the `ENGRAM_` prefix. Defaults work out
of the box for local development.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENGRAM_DB_PATH` | `~/.engram/engram.db` | Database location |
| `ENGRAM_HOST` | `127.0.0.1` | Bind address |
| `ENGRAM_PORT` | `8741` | Listen port |
| `ENGRAM_EMBEDDING_PROVIDER` | `local` | `local` or `openai` |
| `ENGRAM_OPENAI_API_KEY` | — | Required for OpenAI embeddings |
| `ENGRAM_ENCRYPTION_ENABLED` | `false` | AES-256 field encryption |
| `ENGRAM_LOG_LEVEL` | `INFO` | Logging verbosity |

To use OpenAI embeddings instead of the local model:

```bash
export ENGRAM_EMBEDDING_PROVIDER=openai
export ENGRAM_OPENAI_API_KEY=sk-...
```

## What to store

Engram is most valuable when you store knowledge that would otherwise be lost
between sessions:

- **Architecture decisions** — why you chose X over Y, what tradeoffs you accepted
- **Failed attempts** — what you tried, why it didn't work, what you learned
- **Bug context** — root cause analysis, affected files, workarounds
- **Design rationale** — constraints that aren't obvious from the code
- **Onboarding knowledge** — the things a new contributor would ask about

Don't store things that are already in the code, git history, or existing docs.
Store the *why* and the *context* that surrounds them.

## Next steps

- Browse the [REST API docs](http://localhost:8741/docs) (Swagger UI, available when
  the server is running)
- Read the [README](../README.md) for the full feature list and architecture diagram
- Look at `src/engram/models/base.py` for the complete list of entity types and
  relationship types
