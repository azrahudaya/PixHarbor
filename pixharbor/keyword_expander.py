from collections.abc import Iterable


DEFAULT_TEMPLATES = (
    "{keyword}",
    "industrial {keyword}",
    "power plant {keyword}",
    "{keyword} Indonesia",
    "{keyword} factory",
    "{keyword} pabrik",
    "{keyword} industri",
    "{keyword} geothermal",
    "{keyword} PLTP",
    "{keyword} PLTU",
)

DOMAIN_TERMS = {
    "cooling tower": (
        "menara pendingin",
        "geothermal cooling tower",
        "factory cooling tower",
        "hyperbolic cooling tower",
        "evaporative cooling tower",
        "mechanical draft cooling tower",
        "natural draft cooling tower",
    )
}


def normalize_keyword(keyword: str) -> str:
    return " ".join(keyword.strip().split())


def expand_keywords(
    keyword: str,
    limit: int = 10,
    negative_keywords: Iterable[str] = (),
) -> list[str]:
    normalized = normalize_keyword(keyword)
    if not normalized:
        raise ValueError("Keyword cannot be empty.")

    candidates = [template.format(keyword=normalized) for template in DEFAULT_TEMPLATES]
    candidates.extend(DOMAIN_TERMS.get(normalized.casefold(), ()))

    blocked = [item.casefold() for item in negative_keywords]
    results: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        key = candidate.casefold()
        if key in seen or any(term in key for term in blocked):
            continue
        seen.add(key)
        results.append(candidate)
        if len(results) >= limit:
            break

    return results
