from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class CleanSummary:
    checked: int = 0
    clean: int = 0
    rejected: int = 0
    duplicate: int = 0


def clean_dataset(
    dataset_path: Path,
    min_width: int = 1,
    min_height: int = 1,
    allowed_formats: tuple[str, ...] = ("jpg", "jpeg", "png", "webp"),
) -> CleanSummary:
    raw_dir = dataset_path / "raw"
    clean_dir = dataset_path / "clean" / dataset_path.name.replace("-", "_")
    rejected_dir = dataset_path / "rejected"

    checked = clean = rejected = 0
    duplicate = 0
    allowed = {item.lower().lstrip(".") for item in allowed_formats}
    seen_hashes: set[str] = set()

    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue

        checked += 1
        reason = rejection_reason(path, min_width, min_height, allowed)
        source_name = source_prefix(raw_dir, path)

        if reason:
            move_file(path, rejected_dir / reason, source_name)
            rejected += 1
            continue

        sha256_hash = file_sha256(path)
        if sha256_hash in seen_hashes:
            move_file(path, rejected_dir / "duplicate", source_name)
            duplicate += 1
            rejected += 1
        else:
            seen_hashes.add(sha256_hash)
            copy_file(path, clean_dir, source_name)
            clean += 1

    return CleanSummary(checked=checked, clean=clean, rejected=rejected, duplicate=duplicate)


def rejection_reason(
    path: Path,
    min_width: int,
    min_height: int,
    allowed_formats: set[str],
) -> str | None:
    try:
        with Image.open(path) as image:
            image.load()
            image_format = (image.format or "").lower()
            width, height = image.size
    except (UnidentifiedImageError, OSError):
        return "broken"

    if image_format not in allowed_formats:
        return "invalid_format"
    if width < min_width or height < min_height:
        return "too_small"
    return None


def source_prefix(raw_dir: Path, path: Path) -> str:
    relative = path.relative_to(raw_dir)
    return relative.parts[0] if len(relative.parts) > 1 else "image"


def copy_file(path: Path, directory: Path, prefix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = unique_path(directory / f"{prefix}_{path.name}")
    shutil.copy2(path, target)
    return target


def move_file(path: Path, directory: Path, prefix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = unique_path(directory / f"{prefix}_{path.name}")
    shutil.move(str(path), target)
    return target


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(1, 10_000):
        candidate = path.with_stem(f"{path.stem}_{index}")
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Could not find unique path for {path}")


def file_sha256(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()
