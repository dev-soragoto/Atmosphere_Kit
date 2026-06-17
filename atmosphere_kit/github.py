from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class GitHubError(Exception):
    """Raised when release metadata or asset resolution fails."""

    pass


@dataclass(frozen=True)
class ReleaseAsset:
    """A resolved GitHub release asset with its download URL and tag."""

    url: str
    tag: str
    name: str


class GitHubClient:
    """Small GitHub Releases API client used to locate release assets."""

    def __init__(self, token: str | None = None) -> None:
        """Create a client, defaulting to the GITHUB_TOKEN environment variable."""
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")

    def latest_asset(
        self,
        repo: str,
        *,
        name_pattern: str | None = None,
        url_pattern: str | None = None,
    ) -> ReleaseAsset:
        """Return the first latest-release asset matching the configured patterns."""
        release = self._latest_release(repo)
        tag = str(release.get("tag_name") or "unknown")
        assets = release.get("assets") or []
        name_regex = re.compile(name_pattern) if name_pattern else None
        url_regex = re.compile(url_pattern) if url_pattern else None
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            url = asset.get("browser_download_url")
            name = asset.get("name") or ""
            if not isinstance(url, str):
                continue
            name_matches = name_regex.search(str(name)) if name_regex else True
            url_matches = url_regex.search(url) if url_regex else True
            if name_matches and url_matches:
                return ReleaseAsset(url=url, tag=tag, name=str(name))
        patterns = []
        if name_pattern:
            patterns.append(f"name={name_pattern}")
        if url_pattern:
            patterns.append(f"url={url_pattern}")
        raise GitHubError(
            f"release asset not found: repo={repo} {' '.join(patterns)} tag={tag}"
        )

    @lru_cache(maxsize=None)
    def _latest_release(self, repo: str) -> dict[str, Any]:
        """Fetch and cache the latest release JSON for a GitHub repository."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Atmosphere_Kit",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise GitHubError(f"GitHub API failed for {repo}: HTTP {exc.code}") from exc
        except URLError as exc:
            raise GitHubError(f"GitHub API failed for {repo}: {exc.reason}") from exc
