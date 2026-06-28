from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from pixharbor import __version__

DEFAULT_CONFIG = """dataset_name: my_dataset
main_keyword: example keyword
queries:
  - example keyword
negative_keywords:
  - cartoon
  - icon
  - illustration
sources:
  - openverse
  - wikimedia
output_dir: ./datasets/my-dataset
limit: 100
filters:
  min_width: 640
  min_height: 480
  allowed_formats:
    - jpg
    - jpeg
    - png
    - webp
  remove_duplicates: true
  blur_detection: false
"""

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
def init(force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite pixharbor.yaml.")] = False) -> None:
    """Create a starter PixHarbor config."""
    config_path = Path("pixharbor.yaml")
    datasets_path = Path("datasets")

    if config_path.exists() and not force:
        console.print("pixharbor.yaml already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    datasets_path.mkdir(exist_ok=True)

    console.print("Created pixharbor.yaml")
    console.print("Created datasets/")


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
