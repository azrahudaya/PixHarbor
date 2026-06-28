from pathlib import Path

import httpx

from pixharbor.config import DatasetConfig, FilterConfig
from pixharbor.downloader import download_images
from pixharbor.sources import ImageSearchResult


def config(tmp_path: Path) -> DatasetConfig:
    return DatasetConfig(
        dataset_name="cats",
        main_keyword="cat",
        queries=["cat"],
        sources=["openverse"],
        output_dir=tmp_path / "cats",
        limit=1,
        filters=FilterConfig(min_width=1, min_height=1, allowed_formats=["jpg"]),
    )


def result(url: str = "https://example.test/cat.jpg") -> ImageSearchResult:
    return ImageSearchResult(
        id="1",
        source="openverse",
        query="cat",
        title="Cat",
        page_url="https://example.test/cat",
        image_url=url,
    )


def test_download_images_writes_raw_file(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"jpg")
        )
    )

    downloads = download_images(config(tmp_path), [result()], client)
    download = downloads["https://example.test/cat.jpg"]

    assert download.status == "downloaded"
    assert download.local_path == tmp_path / "cats" / "raw" / "openverse" / "000001.jpg"
    assert download.local_path.read_bytes() == b"jpg"


def test_download_images_rejects_non_image_response(tmp_path: Path) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, headers={"content-type": "text/html"}, content=b"nope")
        )
    )

    downloads = download_images(config(tmp_path), [result()], client)

    assert downloads["https://example.test/cat.jpg"].status == "failed"
