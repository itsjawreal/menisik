from __future__ import annotations

import logging
from dataclasses import dataclass

from src.pr_generator import PRImprovement, generate_pr_improvement
from src.scraper import RepoCandidate


@dataclass
class PatchPlan:
    improvement: PRImprovement


def generate_patch(candidate: RepoCandidate, log: logging.Logger, goal: str = "bugfix") -> PatchPlan:
    return PatchPlan(improvement=generate_pr_improvement(candidate, log, goal=goal))
