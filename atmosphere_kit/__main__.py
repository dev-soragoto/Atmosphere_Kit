from __future__ import annotations

import sys
from pathlib import Path

from .builder import BuildError, Builder
from .config import ConfigError, load_config


def main() -> int:
    """Run the package build from current directory."""
    root = Path.cwd()
    try:
        config = load_config(root / "kit.toml")
        Builder(root, config).build()
    except (BuildError, ConfigError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
