from __future__ import annotations

import logging
from dataclasses import dataclass

from src.pr_generator import fetch_repo_candidate_with_scope, find_pr_target
from src.scraper import RepoCandidate
from src.state import get_security_blacklisted_sources


@dataclass
class RepoDiscoveryResult:
    candidate: RepoCandidate
    reason: str
    mode: str


def discover_repository(
    log: logging.Logger,
    repo: str = "",
    *,
    first_pr: bool = False,
) -> RepoDiscoveryResult:
    if repo:
        candidate = fetch_repo_candidate_with_scope(repo, log, enforce_scope=False)
        return RepoDiscoveryResult(
            candidate=candidate,
            reason="Operator pinned this repository for inspection and dry-run planning.",
            mode="targeted",
        )

    candidate = find_pr_target(get_security_blacklisted_sources(), set(), log, first_pr_mode=first_pr)
    if candidate is None:
        raise RuntimeError("No suitable repository found for discovery.")
    return RepoDiscoveryResult(
        candidate=candidate,
        reason="Search mode selected an active repo with enough local evidence and acceptable contribution scope.",
        mode="search",
    )
