from pathlib import Path

from PIL import Image

from pixharbor.cleaner import clean_dataset


def write_image(path: Path, size: tuple[int, int] = (10, 10), image_format: str = "JPEG") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "green").save(path, image_format)


def test_clean_dataset_copies_valid_images(tmp_path: Path) -> None:
    dataset = tmp_path / "cooling-tower"
    write_image(dataset / "raw" / "openverse" / "000001.jpg")

    summary = clean_dataset(dataset, min_width=5, min_height=5)

    assert summary.checked == 1
    assert summary.clean == 1
    assert (dataset / "clean" / "cooling_tower" / "openverse_000001.jpg").exists()
    assert (dataset / "raw" / "openverse" / "000001.jpg").exists()


def test_clean_dataset_rejects_small_images(tmp_path: Path) -> None:
    dataset = tmp_path / "cats"
    write_image(dataset / "raw" / "openverse" / "000001.jpg", size=(2, 2))

    summary = clean_dataset(dataset, min_width=5, min_height=5)

    assert summary.rejected == 1
    assert (dataset / "rejected" / "too_small" / "openverse_000001.jpg").exists()
    assert not (dataset / "raw" / "openverse" / "000001.jpg").exists()


def test_clean_dataset_rejects_broken_images(tmp_path: Path) -> None:
    dataset = tmp_path / "cats"
    path = dataset / "raw" / "openverse" / "000001.jpg"
    path.parent.mkdir(parents=True)
    path.write_text("not an image", encoding="utf-8")

    summary = clean_dataset(dataset)

    assert summary.rejected == 1
    assert (dataset / "rejected" / "broken" / "openverse_000001.jpg").exists()
