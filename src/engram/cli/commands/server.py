from __future__ import annotations

import click
from rich.console import Console

from engram.config import get_settings

console = Console()


@click.group()
def server():
    """Manage the engram server."""


@server.command()
@click.option("--host", default="127.0.0.1", help="Bind address.")
@click.option("--port", default=8741, type=int, help="Port number.")
def start(host, port):
    """Start the engram server."""
    import uvicorn

    from engram.api.app import create_app

    console.print(f"[green]Starting engram server on {host}:{port}[/green]")
    uvicorn.run(create_app(), host=host, port=port)


@server.command()
def status():
    """Check if the server is running."""
    import httpx

    settings = get_settings()
    try:
        r = httpx.get(
            f"http://{settings.host}:{settings.port}/api/v1/admin/health",
            timeout=2,
        )
        if r.status_code == 200:
            console.print("[green]Server is running[/green]")
        else:
            console.print(f"[red]Server returned {r.status_code}[/red]")
    except httpx.ConnectError:
        console.print("[red]Server is not running[/red]")
