# pixharbor

![python](https://img.shields.io/badge/python-3.11%2B-2563eb?style=flat-square&logo=python&logoColor=white)
![cli](https://img.shields.io/badge/interface-cli-0ea5e9?style=flat-square&logo=gnubash&logoColor=white)
![computer vision](https://img.shields.io/badge/focus-computer%20vision-1d4ed8?style=flat-square)
![tests](https://img.shields.io/badge/tests-30%20passed-16a34a?style=flat-square)
![license](https://img.shields.io/badge/license-mit-2563eb?style=flat-square)

cli untuk mengumpulkan, membersihkan, dan mengatur image dataset untuk ai dan computer vision.

## status

`v0.1.0` | early development

fitur inti sudah tersedia. api source, downloader, metadata export, dan dataset cleaner masih dapat berubah.

## fitur

- source adapter untuk openverse dan wikimedia
- keyword expansion berbasis template
- yaml config
- image downloader
- metadata jsonl
- ukuran minimum dan duplicate check
- struktur folder dataset yang konsisten
- command `doctor` untuk cek konfigurasi

## install

```bash
git clone https://github.com/azrahudaya/PixHarbor.git
cd PixHarbor
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## penggunaan

```bash
pixharbor --help
pixharbor init
pixharbor doctor
pixharbor sources
pixharbor expand "cooling tower"
pixharbor search "cooling tower" --source openverse --limit 5
pixharbor collect --config examples/cooling_tower.yaml
pixharbor collect --config examples/cooling_tower.yaml --download
pixharbor clean ./datasets/cooling-tower --min-width 640 --min-height 480
```

## development

```bash
pytest -q
ruff check pixharbor tests
```

## struktur

```text
pixharbor/   source code
examples/    contoh konfigurasi
tests/       test suite
```

## batasan

- source adapter masih terbatas
- belum ada distributed download
- belum ada dashboard
- api source dapat berubah sesuai kebijakan masing-masing provider

## roadmap

lihat [roadmap.md](ROADMAP.md).

## kontribusi

issue dan pull request dipersilakan. jelaskan perubahan, cara menguji, dan dampaknya.

## license

mit. lihat [license](LICENSE).
