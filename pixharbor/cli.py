from typing import Annotated

import typer
from rich.console import Console

from pixharbor import __version__

app = typer.Typer(
    help="Collect, clean, and organize image datasets.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"PixHarbor {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, help="Show PixHarbor version."),
    ] = False,
) -> None:
    pass


@app.command()
def expand(keyword: str, limit: int = 10) -> None:
    """Generate simple keyword suggestions."""
    templates = [
        "{keyword}",
        "industrial {keyword}",
        "power plant {keyword}",
        "{keyword} Indonesia",
        "{keyword} factory",
        "{keyword} pabrik",
        "{keyword} industri",
        "{keyword} geothermal",
        "{keyword} PLTP",
        "{keyword} PLTU",
    ]
    for index, query in enumerate(dict.fromkeys(t.format(keyword=keyword) for t in templates), 1):
        if index > limit:
            break
        console.print(f"{index}. {query}")
