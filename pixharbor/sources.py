import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx

OPENVERSE_IMAGES_URL = "https://api.openverse.org/v1/images/"
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
AVAILABLE_SOURCES = ("openverse", "wikimedia")


class SourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImageSearchResult:
    id: str
    source: str
    query: str
    title: str
    page_url: str
    image_url: str
    thumbnail_url: str | None = None
    author: str | None = None
    license: str | None = None
    width: int | None = None
    height: int | None = None


def list_sources() -> tuple[str, ...]:
    return AVAILABLE_SOURCES


def search_images(
    source: str,
    query: str,
    limit: int = 10,
    client: httpx.Client | None = None,
) -> list[ImageSearchResult]:
    source = source.lower()
    if source == "openverse":
        return search_openverse(query, limit, client)
    if source == "wikimedia":
        return search_wikimedia(query, limit, client)
    raise SourceError(f"Unknown source: {source}")


def search_openverse(
    query: str,
    limit: int = 10,
    client: httpx.Client | None = None,
) -> list[ImageSearchResult]:
    data = _get_json(
        OPENVERSE_IMAGES_URL,
        {"q": query, "page_size": limit},
        client,
    )
    return [
        ImageSearchResult(
            id=str(item.get("id") or ""),
            source="openverse",
            query=query,
            title=item.get("title") or "Untitled",
            page_url=item.get("foreign_landing_url") or "",
            image_url=item.get("url") or "",
            thumbnail_url=item.get("thumbnail"),
            author=item.get("creator"),
            license=item.get("license"),
            width=item.get("width"),
            height=item.get("height"),
        )
        for item in data.get("results", [])
        if item.get("url")
    ]


def search_wikimedia(
    query: str,
    limit: int = 10,
    client: httpx.Client | None = None,
) -> list[ImageSearchResult]:
    data = _get_json(
        WIKIMEDIA_API_URL,
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|user|extmetadata",
            "iiurlwidth": 300,
            "format": "json",
            "formatversion": 2,
        },
        client,
        headers={"User-Agent": os.getenv("WIKIMEDIA_USER_AGENT", "PixHarbor/0.1.0")},
    )
    pages = data.get("query", {}).get("pages", [])
    return [_wikimedia_result(query, page) for page in pages if page.get("imageinfo")]


def _wikimedia_result(query: str, page: dict) -> ImageSearchResult:
    info = page["imageinfo"][0]
    metadata = info.get("extmetadata", {})
    title = page.get("title") or "Untitled"

    return ImageSearchResult(
        id=str(page.get("pageid") or title),
        source="wikimedia",
        query=query,
        title=title.removeprefix("File:"),
        page_url=f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'), safe=':/')}",
        image_url=info.get("url") or "",
        thumbnail_url=info.get("thumburl"),
        author=_metadata_value(metadata, "Artist") or info.get("user"),
        license=_metadata_value(metadata, "LicenseShortName"),
        width=info.get("width"),
        height=info.get("height"),
    )


def _metadata_value(metadata: dict, key: str) -> str | None:
    value = metadata.get(key, {}).get("value")
    return str(value) if value else None


def _get_json(
    url: str,
    params: dict,
    client: httpx.Client | None = None,
    headers: dict | None = None,
) -> dict:
    owns_client = client is None
    active_client = client or httpx.Client(timeout=20, follow_redirects=True)
    try:
        response = active_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise SourceError(str(exc)) from exc
    finally:
        if owns_client:
            active_client.close()
