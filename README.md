# engram

Local-first, vendor-neutral AI memory server for software engineering workflows.

Every AI coding tool (Claude Code, Cursor, Copilot, Codex) builds its own fragmented memory. Engram provides a shared knowledge layer that any tool connects to via REST API or MCP protocol — architecture decisions, bug history, failed attempts, design rationale, and project context all persisted locally in SQLite.

## Features

- **Knowledge Graph** — entities (decisions, bugs, commits, failed attempts, etc.) connected by typed relationships
- **Hybrid Search** — FTS5 full-text + sqlite-vec semantic search combined via Reciprocal Rank Fusion
- **Memory Quality Engine** — importance scoring, near-duplicate detection, conflict detection, temporal decay, background compaction
- **AI Provenance** — full audit trail with point-in-time snapshots for time-travel queries
- **MCP Server** — 10 tools for AI coding assistants (`remember`, `recall`, `record_decision`, `find_contradictions`, etc.)
- **REST API** — FastAPI with OpenAPI docs at `/docs`
- **CLI** — `engram add decision`, `engram search`, `engram admin stats`
- **Web Dashboard** — React SPA with graph explorer, search, and entity detail views
- **Encryption** — optional AES-256 field encryption for sensitive content
- **Ingest Plugins** — git history, markdown files, extensible plugin system
- **Zero Dependencies Beyond Python** — SQLite + sqlite-vec, no external databases

## Quick Start

See the **[Getting Started guide](docs/getting-started.md)** for a full walkthrough
covering installation, first use, MCP setup, and common workflows.

```bash
pip install -e ".[dev]"
engram server start
curl http://localhost:8741/api/v1/admin/health
```

## MCP Configuration

Add to your AI tool's MCP settings (e.g., Claude Code `~/.claude.json`):

```json
{
  "mcpServers": {
    "engram": {
      "command": "python",
      "args": ["-m", "engram.mcp_server.server"],
      "env": {}
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `remember` | Store knowledge — decisions, bugs, snippets, any engineering context |
| `recall` | Semantic search across all memories |
| `recall_about_file` | Find everything known about a specific file |
| `record_decision` | Record an architecture/design decision (ADR) |
| `record_failed_attempt` | Record what was tried and why it failed |
| `get_context` | Get a session-start context bundle (recent decisions, bugs, file knowledge) |
| `get_entity_history` | Full provenance chain for an entity |
| `link_entities` | Create relationships in the knowledge graph |
| `find_contradictions` | Surface conflicting or superseded knowledge |
| `run_quality_check` | Run importance/decay recomputation and archive stale memories |

## CLI

```bash
# Add knowledge
engram add decision "Use SQLite" --project my-project
engram add note "Auth uses JWT tokens" --tags auth,security
engram add failed-attempt "Tried Redis for caching" --why "Too much operational overhead"

# Search
engram search "database architecture"

# Show entity details
engram show <entity-id> --provenance

# Server management
engram server start
engram server status

# Admin
engram admin stats
engram admin reindex
```

## Configuration

Environment variables (prefix `ENGRAM_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENGRAM_DB_PATH` | `~/.engram/engram.db` | SQLite database path |
| `ENGRAM_HOST` | `127.0.0.1` | Server bind address |
| `ENGRAM_PORT` | `8741` | Server port |
| `ENGRAM_EMBEDDING_PROVIDER` | `local` | `local` (sentence-transformers) or `openai` |
| `ENGRAM_OPENAI_API_KEY` | — | Required when using OpenAI embeddings |
| `ENGRAM_ENCRYPTION_ENABLED` | `false` | Enable AES-256 field encryption |
| `ENGRAM_ENCRYPTION_KEY` | — | Fernet key for encryption |
| `ENGRAM_LOG_LEVEL` | `INFO` | Logging level |

## Architecture

```
┌─────────────────────────────────────────────┐
│  AI Tools (Claude Code, Cursor, Copilot)    │
│         ┌──────────┐  ┌──────────┐          │
│         │   MCP    │  │  REST    │          │
│         │  Client  │  │  Client  │          │
│         └────┬─────┘  └────┬─────┘          │
└──────────────┼──────────────┼───────────────┘
               │              │
┌──────────────┼──────────────┼───────────────┐
│  Engram      │              │               │
│         ┌────▼─────┐  ┌────▼─────┐          │
│         │   MCP    │  │  FastAPI │          │
│         │  Server  │  │  Routes  │          │
│         └────┬─────┘  └────┬─────┘          │
│              └──────┬───────┘               │
│                     │                       │
│         ┌───────────▼──────────┐            │
│         │   Hybrid Search      │            │
│         │  (FTS5 + Vec + RRF)  │            │
│         └───────────┬──────────┘            │
│                     │                       │
│    ┌────────┬───────┼───────┬────────┐      │
│    │Entity  │Event  │Vector │FTS     │      │
│    │Store   │Store  │Store  │Store   │      │
│    └────┬───┘───┬───┘───┬───┘───┬────┘      │
│         └───────┴───────┴───────┘           │
│                     │                       │
│            ┌────────▼────────┐              │
│            │     SQLite      │              │
│            │  (WAL + vec)    │              │
│            └─────────────────┘              │
└─────────────────────────────────────────────┘
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/engram/
```

## License

MIT
