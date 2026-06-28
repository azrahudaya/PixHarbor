<p align="center">
  <img src="assets/pixharbor-banner.png" alt="PixHarbor" width="100%">
</p>

# PixHarbor

![Python](https://img.shields.io/badge/Python-3.11%2B-2563EB?style=for-the-badge&logo=python&logoColor=white)
![CLI Tool](https://img.shields.io/badge/CLI-Tool-0EA5E9?style=for-the-badge&logo=terminal&logoColor=white)
![AI Datasets](https://img.shields.io/badge/AI-Datasets-1D4ED8?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-2563EB?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Early_Development-38BDF8?style=for-the-badge)

Open-source CLI tool for collecting, cleaning, and organizing image datasets for AI and computer vision projects.

## Status

PixHarbor is in early development. The first target is `v0.1.0 - Core Collector`.

## Install for Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

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

## MVP Scope

- CLI commands
- Rule-based keyword expansion
- YAML config loading
- Openverse and Wikimedia sources
- Image download workflow
- Metadata export
- Clean dataset folder structure

## License

MIT
