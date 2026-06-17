from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile

from .archive import ArchiveError, extract_archive, make_release_zip
from .config import BuildConfig, PackageConfig
from .downloads import DownloadError, DownloadRequest, Downloader
from .github import GitHubClient, GitHubError
from .resources import copy_resource_tree


class BuildError(Exception):
    """Raised when the build cannot produce a valid release artifact."""

    pass


@dataclass(frozen=True)
class PreparedAsset:
    """A release asset resolved to a temporary download path."""

    name: str
    asset_name: str
    url: str
    tag: str
    output: Path
    target: str | None = None


class Builder:
    """Coordinates the complete SwitchSD build from configuration to zip output."""

    def __init__(self, root: Path, config: BuildConfig) -> None:
        """Initialize paths, clients, and build result tracking."""
        self.root = root
        self.config = config
        self.output_dir = root / config.output_dir
        self.description_path = root / config.description_file
        self.zip_path = root / config.zip_name
        self.github = GitHubClient()
        self.downloader = Downloader()
        self.description_lines: list[str] = []
        self.failures: list[str] = []
        self.completed: set[str] = set()

    def build(self) -> None:
        """Run the full build pipeline and write SwitchSD.zip."""
        self._prepare_output()
        with tempfile.TemporaryDirectory(
            prefix="atmosphere_kit_", dir=self.root
        ) as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            prepared = self._prepare_assets(temp_dir)
            downloaded = self._download_assets(prepared)
            self._install_packages(downloaded)

        self._validate_required()
        self._write_description()
        self._copy_resources()
        self._finalize()
        make_release_zip(self.output_dir, self.zip_path)
        self._print_summary()

    def _prepare_output(self) -> None:
        """Remove old outputs and create the configured base directory structure."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        if self.description_path.exists():
            self.description_path.unlink()
        if self.zip_path.exists():
            self.zip_path.unlink()
        self.output_dir.mkdir()
        for directory in self.config.directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)

    def _prepare_assets(self, temp_dir: Path) -> dict[str, list[PreparedAsset]]:
        """Resolve all configured packages into concrete release assets."""
        prepared: dict[str, list[PreparedAsset]] = {}
        for package in self.config.packages:
            try:
                prepared[package.name] = self._prepare_package_assets(package, temp_dir)
            except GitHubError as exc:
                self._record_failure(package.name, str(exc))
                prepared[package.name] = []
        return prepared

    def _prepare_package_assets(
        self, package: PackageConfig, temp_dir: Path
    ) -> list[PreparedAsset]:
        """Resolve one package into one or more downloadable assets."""
        if package.kind == "multi_file":
            assets: list[PreparedAsset] = []
            for index, asset in enumerate(package.assets):
                release_asset = self.github.latest_asset(
                    package.repo,
                    name_pattern=asset.name_pattern,
                    url_pattern=asset.url_pattern,
                )
                output = temp_dir / _safe_name(package.name, index, release_asset.name)
                assets.append(
                    PreparedAsset(
                        name=package.name,
                        asset_name=release_asset.name,
                        url=release_asset.url,
                        tag=release_asset.tag,
                        output=output,
                        target=asset.target,
                    )
                )
            return assets

        if not package.name_pattern and not package.url_pattern:
            raise BuildError(f"{package.name}: missing name_pattern or url_pattern")
        release_asset = self.github.latest_asset(
            package.repo,
            name_pattern=package.name_pattern,
            url_pattern=package.url_pattern,
        )
        suffix = Path(release_asset.name).suffix or ".download"
        output = temp_dir / f"{_safe_stem(package.name)}{suffix}"
        return [
            PreparedAsset(
                name=package.name,
                asset_name=release_asset.name,
                url=release_asset.url,
                tag=release_asset.tag,
                output=output,
                target=package.target,
            )
        ]

    def _download_assets(
        self, prepared: dict[str, list[PreparedAsset]]
    ) -> dict[str, list[PreparedAsset]]:
        """Download resolved assets concurrently and return successful downloads."""
        flat = [asset for assets in prepared.values() for asset in assets]
        completed: dict[str, list[PreparedAsset]] = {name: [] for name in prepared}
        if not flat:
            return completed

        with ThreadPoolExecutor(
            max_workers=self.config.max_parallel_downloads
        ) as executor:
            future_to_asset = {
                executor.submit(
                    self.downloader.download,
                    DownloadRequest(
                        f"{asset.name}: {asset.asset_name}",
                        asset.url,
                        asset.output,
                    ),
                ): asset
                for asset in flat
            }
            for future in as_completed(future_to_asset):
                asset = future_to_asset[future]
                try:
                    future.result()
                    completed.setdefault(asset.name, []).append(asset)
                    print(f"{asset.name}: {asset.asset_name} download success.")
                except DownloadError as exc:
                    self._record_failure(asset.name, str(exc))

        for assets in completed.values():
            assets.sort(key=lambda item: str(item.output))
        return completed

    def _install_packages(self, downloaded: dict[str, list[PreparedAsset]]) -> None:
        """Install each package into SwitchSD in configuration order."""
        for package in self.config.packages:
            assets = downloaded.get(package.name, [])
            expected_count = len(package.assets) if package.kind == "multi_file" else 1
            if len(assets) != expected_count:
                self._record_failure(package.name, "not all assets downloaded")
                continue
            try:
                self._install_package(package, assets)
            except (
                ArchiveError,
                BuildError,
                OSError,
                subprocess.CalledProcessError,
            ) as exc:
                self._record_failure(package.name, str(exc))
                continue
            self._record_item(package.name, assets[0].tag)

    def _install_package(
        self, package: PackageConfig, assets: list[PreparedAsset]
    ) -> None:
        """Apply one package's archive/file install behavior and post-actions."""
        if package.kind == "archive":
            extract_archive(assets[0].output, self.output_dir)
            assets[0].output.unlink(missing_ok=True)
        elif package.kind in {"file", "multi_file"}:
            for asset in assets:
                if not asset.target:
                    raise BuildError(f"{package.name}: missing target")
                target = self.output_dir / asset.target
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(asset.output), target)
        else:
            raise BuildError(f"{package.name}: unknown kind {package.kind}")

        for action in package.actions:
            self._run_action(action)

    def _run_action(self, action: str) -> None:
        """Run a named package post-install action."""
        if action == "copy_sdout_root":
            sdout = self.output_dir / "SdOut"
            if sdout.is_dir():
                _copy_children(sdout, self.output_dir)
                shutil.rmtree(sdout)
            return
        if action == "generate_sysclk_toolbox":
            sysclk_dir = self.output_dir / "atmosphere/contents/00FF0000636C6BFF"
            toolbox = sysclk_dir / "toolbox.json"
            if (sysclk_dir / "exefs.nsp").is_file() and not toolbox.exists():
                source = self.root / "resources/toolbox/sys-clk.json"
                toolbox.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, toolbox)
            return
        raise BuildError(f"unknown action: {action}")

    def _copy_resources(self) -> None:
        """Copy static configuration resources into the generated SD tree."""
        copy_resource_tree(self.root / "resources", self.output_dir)
        emummc_hosts = self.output_dir / "atmosphere/hosts/emummc.txt"
        sysmmc_hosts = self.output_dir / "atmosphere/hosts/sysmmc.txt"
        if emummc_hosts.exists():
            shutil.copy2(emummc_hosts, sysmmc_hosts)

    def _finalize(self) -> None:
        """Apply final SD tree cleanup, payload rename, and metadata copies."""
        hekate_bins = sorted(self.output_dir.rglob("*hekate_ctcaer*.bin"))
        if hekate_bins:
            shutil.move(str(hekate_bins[0]), self.output_dir / "payload.bin")
        else:
            self._record_failure(
                "Rename hekate_ctcaer_*.bin to payload.bin", "not found"
            )

        for relative in ("switch/haze.nro", "switch/reboot_to_payload.nro"):
            (self.output_dir / relative).unlink(missing_ok=True)

        contents = self.output_dir / "atmosphere/contents"
        if contents.is_dir():
            for flag in contents.rglob("boot2.flag"):
                flag.unlink()
            ovlloader = self._find_ovlloader_dir(contents)
            if ovlloader is None:
                self._record_failure("nx-ovlloader boot2 enable", "not found")
            else:
                flags = ovlloader / "flags"
                flags.mkdir(parents=True, exist_ok=True)
                (flags / "boot2.flag").touch()

        for name in ("README.md", "LICENSE"):
            source = self.root / name
            if source.exists():
                _copy_text_lf(source, self.output_dir / name)

        if self.description_path.exists():
            shutil.copy2(self.description_path, self.output_dir / "description.txt")

    def _find_ovlloader_dir(self, contents: Path) -> Path | None:
        """Find the nx-ovlloader title directory inside atmosphere/contents."""
        for title_dir in sorted(path for path in contents.iterdir() if path.is_dir()):
            if title_dir.name.startswith("420000000007E51A"):
                return title_dir
        return None

    def _validate_required(self) -> None:
        """Fail the build when any configured required component is missing."""
        missing = [name for name in self.config.required if name not in self.completed]
        if missing:
            for name in missing:
                self._record_failure(name, "required component missing")
            raise BuildError("required components are missing: " + ", ".join(missing))

    def _write_description(self) -> None:
        """Write the release description using normalized LF line endings."""
        _write_text_lf(self.description_path, "\n".join(self.description_lines) + "\n")

    def _record_item(self, name: str, version: str) -> None:
        """Record a successfully installed package for description and validation."""
        self.completed.add(name)
        self.description_lines.append(f"{name} ({version or 'unknown'})")

    def _record_failure(self, name: str, reason: str) -> None:
        """Record and print a package or finalization failure once."""
        if name not in self.failures:
            self.failures.append(name)
        print(f"{name} failed: {reason}")

    def _print_summary(self) -> None:
        """Print the final build success/failure summary."""
        if not self.failures:
            print("All downloads completed without recorded failures.")
        else:
            print(f"Some downloads failed ({len(self.failures)}):")
            for item in self.failures:
                print(f" - {item}")
        print("Setup completed successfully.")


def _copy_children(source: Path, destination: Path) -> None:
    """Copy immediate children from one directory into another."""
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            _merge_tree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _merge_tree(source: Path, destination: Path) -> None:
    """Recursively merge a source directory into an existing destination."""
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            _merge_tree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _safe_name(package_name: str, index: int, asset_name: str) -> str:
    """Create a safe temporary filename for a resolved package asset."""
    suffix = Path(asset_name).suffix or ".download"
    return f"{_safe_stem(package_name)}_{index}{suffix}"


def _safe_stem(name: str) -> str:
    """Convert a display name into a filesystem-safe temporary name stem."""
    return (
        "".join(char if char.isalnum() else "_" for char in name).strip("_") or "asset"
    )


def _copy_text_lf(source: Path, target: Path) -> None:
    """Copy a UTF-8 text file while normalizing line endings to LF."""
    text = source.read_text(encoding="utf-8")
    _write_text_lf(target, text)


def _write_text_lf(target: Path, text: str) -> None:
    """Write UTF-8 text with LF line endings regardless of platform."""
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    with target.open("w", encoding="utf-8", newline="\n") as file:
        file.write(normalized)
