from __future__ import annotations

"""Compatibility exports for the contribution engine modules.

Older PR code and tests import from src.pr_engine. New code should prefer the
domain modules directly: contribution_store, opportunity_engine, and
repo_intelligence.
"""

from src.contribution_store import ContributionStore, PREngineStore, PR_ENGINE_DB_FILE
from src.opportunity_engine import (
    Opportunity,
    PatternScanner,
    QualificationResult,
    qualify_opportunity,
)
from src.repo_intelligence import RepoShortlister

__all__ = [
    "ContributionStore",
    "Opportunity",
    "PREngineStore",
    "PR_ENGINE_DB_FILE",
    "PatternScanner",
    "QualificationResult",
    "RepoShortlister",
    "qualify_opportunity",
]
