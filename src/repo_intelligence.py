from __future__ import annotations

from src.contribution_store import ContributionStore
from src.scraper import RepoCandidate


class RepoShortlister:
    def __init__(self, store: ContributionStore) -> None:
        self.store = store

    def score(self, candidate: RepoCandidate, base_score: int) -> int:
        return base_score + self.store.repo_score_adjustment(candidate.full_name)
