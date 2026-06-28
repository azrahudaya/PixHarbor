import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from pixharbor.config import DatasetConfig
from pixharbor.downloader import DownloadResult
from pixharbor.sources import ImageSearchResult


def write_metadata_jsonl(
    config: DatasetConfig,
    results: list[ImageSearchResult],
    downloads: Mapping[str, DownloadResult] | None = None,
    path: Path | None = None,
) -> Path:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = path or output_dir / "metadata.jsonl"

    with metadata_path.open("w", encoding="utf-8") as file:
        for result in results:
            row = asdict(result)
            download = downloads.get(result.image_url) if downloads else None
            row["dataset_name"] = config.dataset_name
            row["local_path"] = str(download.local_path) if download and download.local_path else None
            row["status"] = download.status if download else "found"
            row["error"] = download.error if download else None
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    return metadata_path
