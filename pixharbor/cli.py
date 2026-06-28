import importlib.util
from pathlib import Path
import sys
from typing import Annotated

import typer
from rich.console import Console

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
    help="Collect, clean, and organize image datasets.",
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
def doctor(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to PixHarbor YAML config."),
    ] = Path("pixharbor.yaml"),
) -> None:
    """Check PixHarbor setup."""
    failed = False
    python_ok = sys.version_info >= (3, 11)

    console.print("PixHarbor doctor")
    console.print(f"{'OK' if python_ok else 'FAIL'} Python {sys.version.split()[0]}")
    failed = failed or not python_ok

    for name, module in REQUIRED_MODULES.items():
        ok = importlib.util.find_spec(module) is not None
        console.print(f"{'OK' if ok else 'FAIL'} {name}")
        failed = failed or not ok

    try:
        loaded = load_config(config)
        console.print(f"OK config: {config}")
        console.print(f"OK dataset: {loaded.dataset_name}")
    except ConfigError as exc:
        console.print(f"FAIL config: {exc}")
        failed = True

    if failed:
        raise typer.Exit(1)


@app.command()
def sources() -> None:
    """Show available image sources."""
    for source in list_sources():
        console.print(source)


@app.command()
def search(
    query: str,
    source: Annotated[str, typer.Option("--source", "-s", help="Image source.")] = "openverse",
    limit: Annotated[int, typer.Option("--limit", "-l", min=1, max=50)] = 5,
) -> None:
    """Search image metadata without downloading files."""
    try:
        results = search_images(source, query, limit)
    except SourceError as exc:
        console.print(str(exc))
        raise typer.Exit(1) from exc

    if not results:
        console.print("No results.")
        return

    for index, item in enumerate(results, 1):
        console.print(f"{index}. {item.source}: {item.title}")
        console.print(f"   {item.image_url}")


@app.command()
def collect(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to PixHarbor YAML config."),
    ],
    download: Annotated[bool, typer.Option("--download", help="Download found images.")] = False,
) -> None:
    """Collect image metadata from configured sources."""
    try:
        loaded = load_config(config)
    except ConfigError as exc:
        console.print(str(exc))
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
    if downloads:
        downloaded = sum(1 for item in downloads.values() if item.status == "downloaded")
        console.print(f"Downloaded {downloaded}/{len(results)} images")

    metadata_path = write_metadata_jsonl(loaded, results, downloads)
    console.print(f"Collected {len(results)} image records")
    console.print(f"Wrote {metadata_path}")


@app.command()
def clean(
    dataset_path: Path,
    min_width: Annotated[int, typer.Option("--min-width", min=1)] = 1,
    min_height: Annotated[int, typer.Option("--min-height", min=1)] = 1,
) -> None:
    """Clean downloaded images into clean/ and rejected/ folders."""
    summary = clean_dataset(dataset_path, min_width=min_width, min_height=min_height)
    console.print(f"Checked {summary.checked} images")
    console.print(f"Clean {summary.clean}")
    console.print(f"Rejected {summary.rejected}")


@app.command()
def expand(keyword: str, limit: int = 10) -> None:
    """Generate simple keyword suggestions."""
    try:
        queries = expand_keywords(keyword, limit)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(1) from exc

    for index, query in enumerate(queries, 1):
        console.print(f"{index}. {query}")
