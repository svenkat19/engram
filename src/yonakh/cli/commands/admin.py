from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from yonakh.config import get_settings
from yonakh.db.engine import init_db
from yonakh.embedding.pipeline import EmbeddingPipeline, get_embedding_provider
from yonakh.store.entity_store import EntityStore
from yonakh.store.fts_store import FTSStore
from yonakh.store.vector_store import VectorStore

console = Console()


@click.group()
def admin():
    """Admin commands."""


@admin.command()
def stats():
    """Show database statistics."""
    conn = init_db(get_settings().db_path)

    counts = {}
    for label, sql in [
        ("entities", "SELECT COUNT(*) FROM entities"),
        ("events", "SELECT COUNT(*) FROM events"),
        ("relationships", "SELECT COUNT(*) FROM relationships"),
        ("provenance", "SELECT COUNT(*) FROM provenance"),
    ]:
        try:
            row = conn.execute(sql).fetchone()
            counts[label] = row[0] if row else 0
        except Exception:
            counts[label] = "n/a"

    vs = VectorStore(conn)
    counts["embeddings"] = vs.count() if vs.available else "n/a"

    table = Table(title="Engram Statistics")
    table.add_column("Table", style="bold")
    table.add_column("Count", justify="right", style="cyan")
    for label, count in counts.items():
        table.add_row(label, str(count))
    console.print(table)


@admin.command()
def reindex():
    """Rebuild search indexes."""
    conn = init_db(get_settings().db_path)
    entity_store = EntityStore(conn)
    fts_store = FTSStore(conn)

    console.print("Rebuilding FTS index...")
    fts_store.rebuild()
    console.print("[green]FTS index rebuilt.[/green]")

    vs = VectorStore(conn)
    if not vs.available:
        console.print("[yellow]Vector search not available; skipping re-embed.[/yellow]")
        return

    console.print("Re-embedding all entities...")
    from yonakh.models.entities import EntityFilter

    entities = entity_store.list(EntityFilter(limit=1000))
    provider = get_embedding_provider()
    pipeline = EmbeddingPipeline(provider, vs)
    pipeline.batch_index(entities)
    console.print(f"[green]Indexed {len(entities)} entities.[/green]")
