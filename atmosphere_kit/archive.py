from __future__ import annotations

from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile


class ArchiveError(Exception):
    """Raised when an archive cannot be extracted."""

    pass


def extract_archive(archive: Path, destination: Path) -> None:
    """Extract a supported archive into the destination directory."""
    suffix = archive.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(destination)
        return
    if suffix == ".7z":
        if shutil.which("7z") is None:
            raise ArchiveError(f"cannot extract {archive.name}: missing 7z")
        subprocess.run(
            ["7z", "x", str(archive), f"-o{destination}", "-y"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return
    raise ArchiveError(f"unknown archive format: {archive}")


def make_release_zip(source_dir: Path, output: Path) -> None:
    """Create the release zip using source file timestamps explicitly."""
    if output.exists():
        output.unlink()
    entries = sorted(source_dir.rglob("*"))
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zip_file:
        for path in entries:
            arcname = PurePosixPath(source_dir.name) / path.relative_to(source_dir)
            info = zipfile.ZipInfo.from_file(path, arcname.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            if path.is_dir():
                zip_file.writestr(info, b"")
                continue
            with path.open("rb") as file:
                with zip_file.open(info, "w") as target:
                    shutil.copyfileobj(file, target)
