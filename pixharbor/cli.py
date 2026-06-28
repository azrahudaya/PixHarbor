import importlib.util
from pathlib import Path
import sys
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pixharbor import __version__
from pixharbor.cleaner import clean_dataset
from pixharbor.config import ConfigError, load_config
from pixharbor.downloader import download_images
from pixharbor.keyword_expander import expand_keywords
from pixharbor.metadata import write_metadata_jsonl
from pixharbor.sources import SourceError, list_sources, search_images

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
    help="Build clean image datasets from the terminal.",
    no_args_is_help=True,
)
console = Console()
REQUIRED_MODULES = {
    "Typer": "typer",
    "Rich": "rich",
    "HTTPX": "httpx",
    "Pydantic": "pydantic",
    "PyYAML": "yaml",
    "Pillow": "PIL",
    "ImageHash": "imagehash",
    "Jinja2": "jinja2",
}


def print_panel(title: str, body: str, style: str = "blue") -> None:
    console.print(Panel.fit(body, title=title, border_style=style))


def print_summary(title: str, rows: list[tuple[str, str]]) -> None:
    table = Table(title=title, box=box.ROUNDED, border_style="blue", header_style="bold blue")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")
    for item, value in rows:
        table.add_row(item, value)
    console.print(table)


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
    """Create a starter config."""
    config_path = Path("pixharbor.yaml")
    datasets_path = Path("datasets")

    if config_path.exists() and not force:
        print_panel("Nothing changed", "pixharbor.yaml already exists.\nRun: pixharbor init --force", "yellow")
        raise typer.Exit(1)

    config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    datasets_path.mkdir(exist_ok=True)

    print_panel("Project ready", "Created pixharbor.yaml\nCreated datasets/")


@app.command()
def doctor(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to PixHarbor YAML config."),
    ] = Path("pixharbor.yaml"),
) -> None:
    """Check your setup."""
    failed = False
    python_ok = sys.version_info >= (3, 11)

    table = Table(title="PixHarbor Doctor", box=box.ROUNDED, border_style="blue", header_style="bold blue")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="green")

    table.add_row("Python", "OK" if python_ok else "FAIL", sys.version.split()[0])
    failed = failed or not python_ok

    for name, module in REQUIRED_MODULES.items():
        ok = importlib.util.find_spec(module) is not None
        table.add_row(name, "OK" if ok else "FAIL", module)
        failed = failed or not ok

    try:
        loaded = load_config(config)
        table.add_row("Config", "OK", str(config))
        table.add_row("Dataset", "OK", loaded.dataset_name)
    except ConfigError as exc:
        table.add_row("Config", "FAIL", str(exc))
        failed = True

    console.print(table)
    if failed:
        raise typer.Exit(1)


@app.command()
def sources() -> None:
    """List image sources."""
    table = Table(title="Image Sources", box=box.ROUNDED, border_style="blue", header_style="bold blue")
    table.add_column("Source", style="cyan")
    table.add_column("Status", style="green")
    for source in list_sources():
        table.add_row(source, "ready")
    console.print(table)


@app.command()
def search(
    query: str,
    source: Annotated[str, typer.Option("--source", "-s", help="Image source.")] = "openverse",
    limit: Annotated[int, typer.Option("--limit", "-l", min=1, max=50)] = 5,
) -> None:
    """Search image metadata."""
    try:
        results = search_images(source, query, limit)
    except SourceError as exc:
        console.print(f"Search failed: {exc}")
        raise typer.Exit(1) from exc

    if not results:
        print_panel("No results", f"No images found for: {query}", "yellow")
        return

    table = Table(title=f"Results for {query}", box=box.ROUNDED, border_style="blue", header_style="bold blue")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Source", style="green")
    table.add_column("Title")
    table.add_column("Image URL", overflow="fold")
    for index, item in enumerate(results, 1):
        table.add_row(str(index), item.source, item.title, item.image_url)
    console.print(table)


@app.command()
def collect(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to PixHarbor YAML config."),
    ],
    download: Annotated[bool, typer.Option("--download", help="Download found images.")] = False,
) -> None:
    """Collect image records."""
    try:
        loaded = load_config(config)
    except ConfigError as exc:
        console.print(f"Config error: {exc}")
        raise typer.Exit(1) from exc

    results = []
    seen_urls = set()

    for query in loaded.queries:
        if len(results) >= loaded.limit:
            break
        for source in loaded.sources:
            if len(results) >= loaded.limit:
                break
            remaining = loaded.limit - len(results)
            try:
                found = search_images(source, query, remaining)
            except SourceError as exc:
                console.print(f"{source}: {exc}")
                continue

            for item in found:
                if item.image_url in seen_urls:
                    continue
                seen_urls.add(item.image_url)
                results.append(item)
                if len(results) >= loaded.limit:
                    break

    downloads = download_images(loaded, results) if download else None
    downloaded = sum(1 for item in downloads.values() if item.status == "downloaded") if downloads else 0
    metadata_path = write_metadata_jsonl(loaded, results, downloads)
    print_summary(
        "Collect Summary",
        [
            ("Dataset", loaded.dataset_name),
            ("Records", str(len(results))),
            ("Images", f"{downloaded}/{len(results)} downloaded" if download else "metadata only"),
            ("Metadata", str(metadata_path)),
        ],
    )


@app.command()
def clean(
    dataset_path: Path,
    min_width: Annotated[int, typer.Option("--min-width", min=1)] = 1,
    min_height: Annotated[int, typer.Option("--min-height", min=1)] = 1,
) -> None:
    """Clean downloaded images."""
    summary = clean_dataset(dataset_path, min_width=min_width, min_height=min_height)
    print_summary(
        "Clean Summary",
        [
            ("Checked", str(summary.checked)),
            ("Clean", str(summary.clean)),
            ("Rejected", str(summary.rejected)),
            ("Duplicate", str(summary.duplicate)),
        ],
    )


@app.command()
def expand(keyword: str, limit: int = 10) -> None:
    """Suggest search keywords."""
    try:
        queries = expand_keywords(keyword, limit)
    except ValueError as exc:
        console.print(f"Keyword error: {exc}")
        raise typer.Exit(1) from exc

    console.print("[bold blue]Keyword ideas[/]")
    for index, query in enumerate(queries, 1):
        console.print(f"{index}. {query}")
