from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

from engram.config import get_settings
from engram.db.engine import init_db
from engram.embedding.pipeline import EmbeddingPipeline, get_embedding_provider
from engram.models.base import EntityType
from engram.models.entities import EntityCreate
from engram.store.entity_store import EntityStore
from engram.store.vector_store import VectorStore

console = Console()


def _index_entity(conn, entity):
    """Best-effort embedding index; warn and continue on failure."""
    try:
        provider = get_embedding_provider()
        vs = VectorStore(conn)
        pipeline = EmbeddingPipeline(provider, vs)
        pipeline.index_entity(entity)
    except Exception as exc:
        console.print(f"[yellow]Embedding skipped: {exc}[/yellow]")


def _print_created(entity):
    console.print(Panel(
        f"[bold]{entity.title}[/bold]\n"
        f"type: {entity.entity_type.value}  id: {entity.id}",
        title="[green]Created[/green]",
    ))


@click.group()
def add():
    """Add knowledge to engram."""


@add.command()
@click.argument("title")
@click.option("--context", "-c", prompt=True, help="Context for the decision.")
@click.option("--decision", "-d", prompt=True, help="The decision made.")
@click.option("--project", "-p", default=None, help="Project name.")
def decision(title, context, decision, project):
    """Record an architecture decision."""
    conn = init_db(get_settings().db_path)
    store = EntityStore(conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.DECISION,
        title=title,
        content=decision,
        properties={"context": context, "decision": decision},
        project=project,
        created_by="cli",
    ))
    _index_entity(conn, entity)
    _print_created(entity)


@add.command()
@click.argument("title")
@click.option("--content", "-c", default=None, help="Additional details.")
@click.option("--project", "-p", default=None, help="Project name.")
@click.option("--tags", "-t", default=None, help="Comma-separated tags.")
def note(title, content, project, tags):
    """Add a quick note."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    conn = init_db(get_settings().db_path)
    store = EntityStore(conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.SNIPPET,
        title=title,
        content=content,
        project=project,
        tags=tag_list,
        created_by="cli",
    ))
    _index_entity(conn, entity)
    _print_created(entity)


@add.command("failed-attempt")
@click.argument("title")
@click.option("--why", prompt=True, help="Why it failed.")
@click.option("--lessons", prompt=True, help="Lessons learned.")
@click.option("--project", "-p", default=None, help="Project name.")
def failed_attempt(title, why, lessons, project):
    """Record a failed attempt."""
    conn = init_db(get_settings().db_path)
    store = EntityStore(conn)
    entity = store.create(EntityCreate(
        entity_type=EntityType.FAILED_ATTEMPT,
        title=title,
        content=why,
        properties={"why": why, "lessons": lessons},
        project=project,
        created_by="cli",
    ))
    _index_entity(conn, entity)
    _print_created(entity)
