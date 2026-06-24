from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from yonakh.config import get_settings
from yonakh.db.engine import init_db
from yonakh.embedding.pipeline import EmbeddingPipeline, get_embedding_provider
from yonakh.models.base import EntityType
from yonakh.models.search import SearchQuery
from yonakh.search.hybrid import HybridSearch
from yonakh.store.entity_store import EntityStore
from yonakh.store.fts_store import FTSStore
from yonakh.store.vector_store import VectorStore

console = Console()


@click.command("search")
@click.argument("query")
@click.option("--type", "-t", "entity_type", default=None, help="Filter by entity type.")
@click.option("--project", "-p", default=None, help="Filter by project.")
@click.option("--limit", "-l", default=10, type=int, help="Max results.")
def search(query, entity_type, project, limit):
    """Search yonakh's memory."""
    conn = init_db(get_settings().db_path)
    entity_store = EntityStore(conn)
    fts_store = FTSStore(conn)
    provider = get_embedding_provider()
    vs = VectorStore(conn)
    pipeline = EmbeddingPipeline(provider, vs)

    entity_types = [EntityType(entity_type)] if entity_type else None
    sq = SearchQuery(
        query=query,
        entity_types=entity_types,
        project=project,
        limit=limit,
    )

    hs = HybridSearch(entity_store, fts_store, pipeline)
    response = hs.search(sq)

    if not response.results:
        console.print("[dim]No results found.[/dim]")
        return

    table = Table(title=f"Results for '{query}' ({response.total} total, {response.duration_ms:.0f}ms)")
    table.add_column("Score", style="cyan", width=6)
    table.add_column("Type", style="magenta", width=16)
    table.add_column("Title", style="bold")
    table.add_column("Snippet", style="dim", max_width=50)

    for r in response.results:
        snippet = (r.entity.content or "")[:80].replace("\n", " ")
        table.add_row(
            f"{r.score:.3f}",
            r.entity.entity_type.value,
            r.entity.title,
            snippet,
        )

    console.print(table)
