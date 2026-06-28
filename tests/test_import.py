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
