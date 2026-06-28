from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from pixharbor import __version__
from pixharbor.cli import app


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
