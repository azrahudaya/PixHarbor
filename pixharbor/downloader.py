from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from pixharbor.config import DatasetConfig
from pixharbor.sources import ImageSearchResult

CONTENT_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@dataclass(frozen=True)
class DownloadResult:
    image_url: str
    local_path: Path | None
    status: str
    error: str | None = None


def download_images(
    config: DatasetConfig,
    results: list[ImageSearchResult],
    client: httpx.Client | None = None,
) -> dict[str, DownloadResult]:
    # ponytail: sync downloads are enough for MVP; add async when throughput matters.
    owns_client = client is None
    active_client = client or httpx.Client(timeout=30, follow_redirects=True)
    downloads: dict[str, DownloadResult] = {}

    try:
        for index, result in enumerate(results, 1):
            downloads[result.image_url] = download_image(config, result, index, active_client)
    finally:
        if owns_client:
            active_client.close()

    return downloads


def download_image(
    config: DatasetConfig,
    result: ImageSearchResult,
    index: int,
    client: httpx.Client,
) -> DownloadResult:
    try:
        response = client.get(result.image_url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return DownloadResult(result.image_url, None, "failed", str(exc))

    content_type = response.headers.get("content-type", "").split(";")[0].lower()
    if content_type and not content_type.startswith("image/"):
        return DownloadResult(result.image_url, None, "failed", f"invalid content type: {content_type}")
    if not response.content:
        return DownloadResult(result.image_url, None, "failed", "empty response")

    raw_dir = config.output_dir / "raw" / result.source
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{index:06d}{_extension(result.image_url, content_type)}"
    path.write_bytes(response.content)

    return DownloadResult(result.image_url, path, "downloaded")


def _extension(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return CONTENT_EXTENSIONS.get(content_type, ".jpg")
