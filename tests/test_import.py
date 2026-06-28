from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from pixharbor import __version__
from pixharbor.cli import app
from pixharbor.downloader import DownloadResult
from pixharbor.sources import ImageSearchResult


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_expand() -> None:
    result = CliRunner().invoke(app, ["expand", "cooling tower", "--limit", "2"])

    assert result.exit_code == 0
    assert "1. cooling tower" in result.output
    assert "2. industrial cooling tower" in result.output


def test_init_creates_project_files(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init"])

    assert result.exit_code == 0
    assert Path("pixharbor.yaml").exists()
    assert Path("datasets").is_dir()
    assert "Created pixharbor.yaml" in result.output


def test_init_refuses_to_overwrite_config(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    Path("pixharbor.yaml").write_text("custom: true\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["init"])

    assert result.exit_code == 1
    assert Path("pixharbor.yaml").read_text(encoding="utf-8") == "custom: true\n"


def test_init_force_overwrites_config(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    Path("pixharbor.yaml").write_text("custom: true\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["init", "--force"])

    assert result.exit_code == 0
    assert "dataset_name: my_dataset" in Path("pixharbor.yaml").read_text(encoding="utf-8")


def test_doctor_accepts_valid_config(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    CliRunner().invoke(app, ["init"])
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "OK config: pixharbor.yaml" in result.output


def test_doctor_rejects_missing_config(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "FAIL config: Config not found: pixharbor.yaml" in result.output


def test_sources_command() -> None:
    result = CliRunner().invoke(app, ["sources"])

    assert result.exit_code == 0
    assert "openverse" in result.output
    assert "wikimedia" in result.output


def test_search_command(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "pixharbor.cli.search_images",
        lambda source, query, limit: [
            ImageSearchResult(
                id="1",
                source=source,
                query=query,
                title="Cat",
                page_url="https://example.test/cat",
                image_url="https://example.test/cat.jpg",
            )
        ],
    )
    result = CliRunner().invoke(app, ["search", "cat", "--source", "openverse", "--limit", "1"])

    assert result.exit_code == 0
    assert "openverse: Cat" in result.output


def test_collect_writes_metadata(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    Path("pixharbor.yaml").write_text(
        """
dataset_name: cats
main_keyword: cat
queries:
  - cat
negative_keywords: []
sources:
  - openverse
output_dir: ./datasets/cats
limit: 1
filters:
  min_width: 1
  min_height: 1
  allowed_formats:
    - jpg
  remove_duplicates: true
  blur_detection: false
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "pixharbor.cli.search_images",
        lambda source, query, limit: [
            ImageSearchResult(
                id="1",
                source=source,
                query=query,
                title="Cat",
                page_url="https://example.test/cat",
                image_url="https://example.test/cat.jpg",
            )
        ],
    )

    result = CliRunner().invoke(app, ["collect", "--config", "pixharbor.yaml"])

    assert result.exit_code == 0
    assert Path("datasets/cats/metadata.jsonl").exists()
    assert "Collected 1 image records" in result.output


def test_collect_downloads_images(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    Path("pixharbor.yaml").write_text(
        """
dataset_name: cats
main_keyword: cat
queries:
  - cat
negative_keywords: []
sources:
  - openverse
output_dir: ./datasets/cats
limit: 1
filters:
  min_width: 1
  min_height: 1
  allowed_formats:
    - jpg
  remove_duplicates: true
  blur_detection: false
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "pixharbor.cli.search_images",
        lambda source, query, limit: [
            ImageSearchResult(
                id="1",
                source=source,
                query=query,
                title="Cat",
                page_url="https://example.test/cat",
                image_url="https://example.test/cat.jpg",
            )
        ],
    )
    monkeypatch.setattr(
        "pixharbor.cli.download_images",
        lambda config, results: {
            "https://example.test/cat.jpg": DownloadResult(
                "https://example.test/cat.jpg",
                Path("datasets/cats/raw/openverse/000001.jpg"),
                "downloaded",
            )
        },
    )

    result = CliRunner().invoke(app, ["collect", "--config", "pixharbor.yaml", "--download"])

    assert result.exit_code == 0
    assert "Downloaded 1/1 images" in result.output


def test_clean_command(tmp_path: Path) -> None:
    dataset = tmp_path / "cats"
    raw = dataset / "raw" / "openverse"
    raw.mkdir(parents=True)
    raw.joinpath("000001.jpg").write_text("not an image", encoding="utf-8")

    result = CliRunner().invoke(app, ["clean", str(dataset)])

    assert result.exit_code == 0
    assert "Checked 1 images" in result.output
    assert "Rejected 1" in result.output
    assert "Duplicate 0" in result.output
