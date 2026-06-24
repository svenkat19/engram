from __future__ import annotations

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Engram: AI memory server for software engineering."""
    pass


# Import and register subcommands
from yonakh.cli.commands.server import server
from yonakh.cli.commands.add import add
from yonakh.cli.commands.search_cmd import search
from yonakh.cli.commands.show import show
from yonakh.cli.commands.admin import admin

cli.add_command(server)
cli.add_command(add)
cli.add_command(search)
cli.add_command(show)
cli.add_command(admin)
