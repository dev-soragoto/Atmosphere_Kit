from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DownloadError(Exception):
    """Raised when a download fails after all retry attempts."""

    pass


@dataclass(frozen=True)
class DownloadRequest:
    """A concrete URL-to-path download request."""

    name: str
    url: str
    output: Path


class Downloader:
    """HTTP downloader with simple retry behavior."""

    def __init__(self, retries: int = 3, timeout: int = 300) -> None:
        """Configure retry count and per-request timeout in seconds."""
        self.retries = retries
        self.timeout = timeout

    def download(self, request: DownloadRequest) -> None:
        """Download a file to disk, retrying transient network and I/O errors."""
        request.output.parent.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                self._download_once(request)
                return
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(2)
        raise DownloadError(f"{request.name} download failed: {last_error}")

    def _download_once(self, request: DownloadRequest) -> None:
        """Perform one streaming HTTP download attempt."""
        headers = {"User-Agent": "Atmosphere_Kit"}
        http_request = Request(request.url, headers=headers)
        with urlopen(http_request, timeout=self.timeout) as response:
            with request.output.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    file.write(chunk)
