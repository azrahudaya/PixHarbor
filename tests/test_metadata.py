import json
from pathlib import Path

from pixharbor.config import DatasetConfig, FilterConfig
from pixharbor.metadata import write_metadata_jsonl
from pixharbor.sources import ImageSearchResult


def test_write_metadata_jsonl(tmp_path: Path) -> None:
    config = DatasetConfig(
        dataset_name="cats",
        main_keyword="cat",
        queries=["cat"],
        sources=["openverse"],
        output_dir=tmp_path / "cats",
        limit=1,
        filters=FilterConfig(min_width=1, min_height=1, allowed_formats=["jpg"]),
    )
    path = write_metadata_jsonl(
        config,
        [
            ImageSearchResult(
                id="1",
                source="openverse",
                query="cat",
                title="Cat",
                page_url="https://example.test/cat",
                image_url="https://example.test/cat.jpg",
            )
        ],
    )

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert path == tmp_path / "cats" / "metadata.jsonl"
    assert rows[0]["dataset_name"] == "cats"
    assert rows[0]["status"] == "found"
