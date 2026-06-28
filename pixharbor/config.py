from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ConfigError(ValueError):
    pass


class FilterConfig(BaseModel):
    min_width: int = Field(ge=1)
    min_height: int = Field(ge=1)
    allowed_formats: list[str] = Field(min_length=1)
    remove_duplicates: bool = True
    blur_detection: bool = False

    @field_validator("allowed_formats")
    @classmethod
    def normalize_formats(cls, formats: list[str]) -> list[str]:
        return [item.lower().lstrip(".") for item in formats]


class DatasetConfig(BaseModel):
    dataset_name: str = Field(min_length=1)
    main_keyword: str = Field(min_length=1)
    queries: list[str] = Field(min_length=1)
    negative_keywords: list[str] = Field(default_factory=list)
    sources: list[str] = Field(min_length=1)
    output_dir: Path
    limit: int = Field(ge=1)
    filters: FilterConfig


def load_config(path: Path) -> DatasetConfig:
    try:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        return DatasetConfig.model_validate(data)
    except FileNotFoundError as exc:
        raise ConfigError(f"Config not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML: {exc}") from exc
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
