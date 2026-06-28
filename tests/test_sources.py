import httpx
import pytest

from pixharbor.sources import SourceError, list_sources, search_images, search_openverse, search_wikimedia


def mock_client(payload: dict) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)))


def test_list_sources() -> None:
    assert list_sources() == ("openverse", "wikimedia")


def test_search_images_rejects_unknown_source() -> None:
    with pytest.raises(SourceError):
        search_images("nope", "cat")


def test_search_images_accepts_uppercase_source() -> None:
    results = search_images("OPENVERSE", "cat", client=mock_client({"results": []}))

    assert results == []


def test_search_openverse_normalizes_results() -> None:
    results = search_openverse(
        "cat",
        client=mock_client(
            {
                "results": [
                    {
                        "id": "abc",
                        "title": "Cat",
                        "foreign_landing_url": "https://example.test/cat",
                        "url": "https://example.test/cat.jpg",
                        "thumbnail": "https://example.test/thumb.jpg",
                        "creator": "Ada",
                        "license": "cc0",
                        "width": 800,
                        "height": 600,
                    }
                ]
            }
        ),
    )

    assert results[0].source == "openverse"
    assert results[0].title == "Cat"
    assert results[0].image_url == "https://example.test/cat.jpg"


def test_search_wikimedia_normalizes_results() -> None:
    results = search_wikimedia(
        "cat",
        client=mock_client(
            {
                "query": {
                    "pages": [
                        {
                            "pageid": 1,
                            "title": "File:Cat image.jpg",
                            "imageinfo": [
                                {
                                    "url": "https://upload.wikimedia.org/cat.jpg",
                                    "thumburl": "https://upload.wikimedia.org/thumb.jpg",
                                    "user": "Ada",
                                    "width": 800,
                                    "height": 600,
                                    "extmetadata": {
                                        "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                        "Artist": {"value": "Ada"},
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        ),
    )

    assert results[0].source == "wikimedia"
    assert results[0].title == "Cat image.jpg"
    assert results[0].license == "CC BY-SA 4.0"
