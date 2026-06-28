# PixHarbor

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
pixharbor expand "cooling tower"
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
