from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib


class ConfigError(Exception):
    """Raised when kit.toml is missing, malformed, or semantically invalid."""

    pass


@dataclass(frozen=True)
class AssetConfig:
    """One downloadable release asset inside a multi-file package."""

    name_pattern: str | None
    url_pattern: str | None
    target: str


@dataclass(frozen=True)
class PackageConfig:
    """One configured component to resolve, download, and install."""

    group: str
    name: str
    repo: str
    kind: str
    name_pattern: str | None = None
    url_pattern: str | None = None
    target: str | None = None
    assets: tuple[AssetConfig, ...] = ()
    actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildConfig:
    """Top-level build settings and package list from kit.toml."""

    output_dir: str
    zip_name: str
    description_file: str
    max_parallel_downloads: int
    required: tuple[str, ...]
    directories: tuple[str, ...]
    packages: tuple[PackageConfig, ...] = field(default_factory=tuple)


def load_config(path: Path) -> BuildConfig:
    """Load kit.toml and convert it into validated dataclass objects."""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"missing config file: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc

    build = raw.get("build")
    if not isinstance(build, dict):
        raise ConfigError("missing [build] section")

    packages_raw = raw.get("packages")
    if not isinstance(packages_raw, list) or not packages_raw:
        raise ConfigError("missing [[packages]] entries")

    packages = tuple(_parse_package(item) for item in packages_raw)
    required = tuple(_string_list(build, "required"))
    directories = tuple(_string_list(build, "directories"))
    max_parallel = int(build.get("max_parallel_downloads", 5))
    if max_parallel < 1:
        raise ConfigError("build.max_parallel_downloads must be >= 1")

    return BuildConfig(
        output_dir=_string(build, "output_dir"),
        zip_name=_string(build, "zip_name"),
        description_file=_string(build, "description_file"),
        max_parallel_downloads=max_parallel,
        required=required,
        directories=directories,
        packages=packages,
    )


def _parse_package(raw: dict[str, Any]) -> PackageConfig:
    """Parse one [[packages]] TOML table."""
    kind = _string(raw, "kind")
    assets = tuple(_parse_asset(item) for item in raw.get("assets", []))
    package = PackageConfig(
        group=_string(raw, "group"),
        name=_string(raw, "name"),
        repo=_string(raw, "repo"),
        kind=kind,
        name_pattern=_optional_string(raw, "name_pattern"),
        url_pattern=_optional_string(raw, "url_pattern"),
        target=raw.get("target"),
        assets=assets,
        actions=tuple(_string_list(raw, "actions", required=False)),
    )
    _validate_package(package)
    return package


def _parse_asset(raw: dict[str, Any]) -> AssetConfig:
    """Parse one [[packages.assets]] TOML table."""
    return AssetConfig(
        name_pattern=_optional_string(raw, "name_pattern"),
        url_pattern=_optional_string(raw, "url_pattern"),
        target=_string(raw, "target"),
    )


def _validate_package(package: PackageConfig) -> None:
    """Validate package fields that depend on the selected package kind."""
    if package.kind in {"archive", "file"}:
        if not package.name_pattern and not package.url_pattern:
            raise ConfigError(
                f"{package.name}: {package.kind} requires name_pattern or url_pattern"
            )
    if package.kind == "file" and not package.target:
        raise ConfigError(f"{package.name}: file package requires target")
    if package.kind == "multi_file" and not package.assets:
        raise ConfigError(f"{package.name}: multi_file package requires assets")
    for asset in package.assets:
        if not asset.name_pattern and not asset.url_pattern:
            raise ConfigError(
                f"{package.name}: each asset requires name_pattern or url_pattern"
            )
    if package.kind not in {"archive", "file", "multi_file"}:
        raise ConfigError(f"{package.name}: unknown package kind {package.kind!r}")


def _string(raw: dict[str, Any], key: str) -> str:
    """Read a required non-empty string field."""
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"missing string field: {key}")
    return value


def _optional_string(raw: dict[str, Any], key: str) -> str | None:
    """Read an optional non-empty string field."""
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{key} must be a non-empty string")
    return value


def _string_list(raw: dict[str, Any], key: str, required: bool = True) -> list[str]:
    """Read a string list field, optionally allowing it to be absent."""
    value = raw.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{key} must be a list of strings")
    return value
