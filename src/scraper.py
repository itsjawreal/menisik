from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
_GITHUB_API = "https://api.github.com"
_ALLOWED_LICENSES = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "unlicense"}
_MAX_REPO_FILES = int(os.getenv("CONTRIB_MAX_REPO_FILES", "120"))
_MAX_FILE_BYTES = int(os.getenv("CONTRIB_MAX_FILE_BYTES", "500000"))
_SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".zip",
    ".tar",
    ".gz",
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
}
_SKIP_DIRS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".tox",
    "dist",
    "build",
    ".eggs",
}


# ── Data models ──────────────────────────────────────────────
@dataclass
class RepoCandidate:
    name: str
    full_name: str
    description: str
    stars: int
    forks: int
    license: str
    url: str
    default_branch: str
    pushed_days_ago: int
    topics: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)


class ScraperError(Exception):
    """Raised when GitHub API or source download fails."""


# ── GitHub API ───────────────────────────────────────────────
def _gh_headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request_proxies() -> dict[str, str]:
    blocked_proxy = "http://127.0.0.1:9"
    candidates = {
        "http": os.getenv("HTTP_PROXY", "").strip(),
        "https": os.getenv("HTTPS_PROXY", "").strip(),
    }
    return {
        scheme: value
        for scheme, value in candidates.items()
        if value and value.lower() != blocked_proxy
    }


def _http_get(url: str, **kwargs) -> requests.Response:
    session = requests.Session()
    session.trust_env = False
    try:
        return session.get(url, **kwargs)
    finally:
        session.close()


def _wait_for_rate_limit(resp: requests.Response) -> None:
    reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
    now = int(time.time())
    wait_secs = max(10, (reset_ts - now) + 5) if reset_ts else 3600
    log.warning("GitHub rate limit hit; waiting %ds for reset", wait_secs)
    time.sleep(wait_secs)


def _gh_get(url: str, params: dict | None = None, timeout: int = 15, _retry: int = 0) -> Any:
    try:
        resp = _http_get(
            url,
            headers=_gh_headers(),
            params=params,
            timeout=timeout,
            proxies=_request_proxies(),
        )
    except requests.exceptions.Timeout:
        if _retry < 2:
            wait = 10 * (2 ** _retry)
            log.warning("GitHub API timeout; retry %d/2 in %ds", _retry + 1, wait)
            time.sleep(wait)
            return _gh_get(url, params, timeout * 2, _retry + 1)
        raise

    if resp.status_code in (403, 429):
        body = resp.text.lower()
        if "rate limit" in body or "secondary rate" in body or resp.status_code == 429:
            _wait_for_rate_limit(resp)
            if _retry < 2:
                return _gh_get(url, params, timeout, _retry + 1)
        raise ScraperError(f"GitHub API auth error ({resp.status_code}): {resp.text[:200]}")
    if resp.status_code == 404:
        raise ScraperError(f"GitHub API 404: {url}")
    resp.raise_for_status()
    return resp.json()


def _get_license(repo: dict) -> str:
    lic = repo.get("license") or {}
    return (lic.get("spdx_id") or "").lower()


def _metadata_security_ok(candidate: RepoCandidate) -> bool:
    haystack = " ".join(
        [
            candidate.name,
            candidate.description,
            " ".join(candidate.topics),
        ]
    ).lower()
    suspicious = ("crack", "stealer", "malware", "phishing", "token grabber", "keylogger")
    return not any(marker in haystack for marker in suspicious)


# ── Source download ──────────────────────────────────────────
def _should_skip_path(path: str, size: int) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in _SKIP_DIRS for part in parts):
        return True
    if Path(normalized).suffix.lower() in _SKIP_EXTENSIONS:
        return True
    return size > _MAX_FILE_BYTES


def _decode_blob(content: str) -> str:
    return base64.b64decode(content.encode("utf-8")).decode("utf-8", errors="replace")


def download_repo_files(candidate: RepoCandidate) -> dict[str, str]:
    tree = _gh_get(
        f"{_GITHUB_API}/repos/{candidate.full_name}/git/trees/{candidate.default_branch}",
        params={"recursive": "1"},
        timeout=30,
    )
    files: dict[str, str] = {}
    skipped = 0
    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        size = int(item.get("size") or 0)
        if not path or _should_skip_path(path, size):
            skipped += 1
            continue
        if not path.endswith((".py", ".ts", ".tsx", ".json", ".toml", ".txt", ".md", ".yml", ".yaml")):
            skipped += 1
            continue
        if len(files) >= _MAX_REPO_FILES:
            skipped += 1
            continue
        blob = _gh_get(f"{_GITHUB_API}/repos/{candidate.full_name}/contents/{path}", params={"ref": candidate.default_branch})
        encoded = blob.get("content", "")
        if blob.get("encoding") != "base64" or not encoded:
            skipped += 1
            continue
        files[path] = _decode_blob(encoded)

    log.info("Download complete: %d files downloaded, %d skipped", len(files), skipped)
    return files


def repo_from_api_payload(item: dict) -> RepoCandidate:
    pushed_days_ago = 999
    pushed_at = item.get("pushed_at", "")
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        pushed_days_ago = (datetime.now(timezone.utc) - pushed).days
    except Exception:
        pass

    return RepoCandidate(
        name=item["name"],
        full_name=item["full_name"],
        description=(item.get("description") or "")[:200],
        stars=item.get("stargazers_count", 0),
        forks=item.get("forks_count", 0),
        license=_get_license(item),
        url=item["html_url"],
        default_branch=item.get("default_branch", "main"),
        pushed_days_ago=pushed_days_ago,
        topics=item.get("topics", []),
    )
