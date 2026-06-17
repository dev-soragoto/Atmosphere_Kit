from __future__ import annotations

from pathlib import Path
import shutil


def copy_resource_tree(resources_root: Path, output_dir: Path) -> None:
    """Copy static SD-card resources into the build output directory."""
    sd_root = resources_root / "sd"
    for source in sorted(path for path in sd_root.rglob("*") if path.is_file()):
        target = output_dir / source.relative_to(sd_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
