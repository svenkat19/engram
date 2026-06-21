from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from engram.config import get_settings
from engram.db.engine import init_db
from engram.store.entity_store import EntityStore
from engram.store.provenance_store import ProvenanceStore

console = Console()


@click.command()
@click.argument("entity_id")
@click.option("--provenance", is_flag=True, help="Show provenance chain.")
def show(entity_id, provenance):
    """Show entity details."""
    conn = init_db(get_settings().db_path)
    store = EntityStore(conn)
    entity = store.get(entity_id)

    if entity is None:
        console.print(f"[red]Entity {entity_id} not found[/red]")
        raise SystemExit(1)

    lines = [
        f"[bold]Title:[/bold] {entity.title}",
        f"[bold]Type:[/bold]  {entity.entity_type.value}",
        f"[bold]Status:[/bold] {entity.status.value}",
    ]
    if entity.project:
        lines.append(f"[bold]Project:[/bold] {entity.project}")
    if entity.tags:
        lines.append(f"[bold]Tags:[/bold] {', '.join(entity.tags)}")
    if entity.content:
        lines.append(f"\n{entity.content}")
    if entity.properties:
        for k, v in entity.properties.items():
            lines.append(f"[bold]{k}:[/bold] {v}")

    lines.append(f"\n[dim]created {entity.created_at:%Y-%m-%d %H:%M} | "
                 f"importance {entity.importance:.2f} | "
                 f"confidence {entity.confidence:.2f}[/dim]")

    console.print(Panel("\n".join(lines), title=entity.id))

    if provenance:
        prov_store = ProvenanceStore(conn)
        records = prov_store.get_for_entity(entity_id)
        if not records:
            console.print("[dim]No provenance records.[/dim]")
            return
        table = Table(title="Provenance")
        table.add_column("Timestamp", style="dim")
        table.add_column("Action", style="cyan")
        table.add_column("Actor")
        table.add_column("Details", max_width=50)
        for rec in records:
            table.add_row(
                f"{rec.timestamp:%Y-%m-%d %H:%M}",
                rec.action.value,
                rec.actor or "",
                str(rec.details) if rec.details else "",
            )
        console.print(table)
