from __future__ import annotations

import logging
from dataclasses import dataclass

from src.contribution_store import ContributionStore


@dataclass
class ContributionRunSummary:
    run_id: int
    submitted: int
    target: int
    attempts: int
    ai_calls: int
    est_tokens: int
    discovered: int
    state_counts: dict
    top_rejections: list
    bottleneck: str = ""


class ContributionEngine:
    """Thin orchestration layer around contribution state and run summaries."""

    def __init__(self, store: ContributionStore) -> None:
        self.store = store
        self.active_run_id: int | None = None

    def start_run(self, mode: str, target_count: int) -> int:
        self.active_run_id = self.store.start_run(mode=mode, target_count=target_count)
        return self.active_run_id

    def finish_run(
        self,
        submitted: int,
        target: int,
        attempts: int,
        usage: dict[str, int],
        log: logging.Logger,
    ) -> dict:
        if self.active_run_id is None:
            return {}

        summary = self.store.summarize_run(self.active_run_id)
        summary.update(
            {
                "run_id": self.active_run_id,
                "submitted": submitted,
                "target": target,
                "attempts": attempts,
                "ai_calls": usage.get("calls", 0),
                "est_tokens": usage.get("est_tokens", 0),
            }
        )
        self.store.finish_run(self.active_run_id, summary)
        self._log_summary(summary, log)
        return summary

    def can_submit_to_repo(self, repo_full_name: str) -> bool:
        return not self.store.has_open_pr(repo_full_name)

    def build_operator_report(self, limit: int = 5) -> str:
        summaries = self.store.latest_run_summaries(limit=limit)
        queued = self.store.queued_opportunities(limit=10)
        if not summaries and not queued:
            return "No contribution engine runs recorded yet."

        latest = summaries[0] if summaries else {}
        lines = [
            "Contribution Engine Report",
            "==========================",
        ]
        if latest:
            submitted = latest.get("submitted", 0)
            target = latest.get("target", 0)
            attempts = latest.get("attempts", 0)
            states = latest.get("state_counts", {})
            headline = f"Latest run #{latest.get('run_id', '?')}: submitted {submitted}/{target} after {attempts} attempt(s)"
            lines.extend(["", headline, f"States: {states}"])
            if latest.get("top_rejections"):
                pretty_rejections = ", ".join(
                    f"{reason} x{count}" for reason, count in latest["top_rejections"][:3]
                )
                lines.append(f"Top rejections: {pretty_rejections}")
            if latest.get("bottleneck"):
                lines.append(f"Bottleneck: {latest['bottleneck']}")

        if summaries:
            lines.append("")
            lines.append("Recent runs:")
            for summary in summaries:
                lines.append(
                    "- run #{run_id}: submitted={submitted}/{target}, attempts={attempts}, "
                    "ai_calls={ai_calls}, states={states}".format(
                        run_id=summary.get("run_id", "?"),
                        submitted=summary.get("submitted", 0),
                        target=summary.get("target", 0),
                        attempts=summary.get("attempts", 0),
                        ai_calls=summary.get("ai_calls", 0),
                        states=summary.get("state_counts", {}),
                    )
                )
                if summary.get("bottleneck"):
                    lines.append(f"  bottleneck: {summary['bottleneck']}")
        if queued:
            lines.append("")
            lines.append(f"Ready queue ({len(queued)} shown):")
            for opportunity in queued:
                lines.append(
                    "- #{id} {repo} {pattern} {file} score={score}".format(
                        id=opportunity.get("id"),
                        repo=opportunity.get("repo_full_name"),
                        pattern=opportunity.get("pattern_type"),
                        file=opportunity.get("target_file"),
                        score=opportunity.get("acceptance_score"),
                    )
                )
        lines.append("")
        lines.append("Suggested next step:")
        if queued:
            lines.append("- Run `python -m app.builder --contrib --1` to consume the strongest queued opportunity.")
        elif latest.get("top_rejections"):
            top_reason = latest["top_rejections"][0][0]
            lines.append(f"- Investigate rejection pattern `{top_reason}` before widening search or targeting larger repos.")
        else:
            lines.append("- Run `python -m app.builder --contrib --1` to start a new contribution cycle.")
        return "\n".join(lines)

    def _log_summary(self, summary: dict, log: logging.Logger) -> None:
        log.info(
            "Contribution run summary: discovered=%d | states=%s | top_rejections=%s",
            summary.get("discovered", 0),
            summary.get("state_counts", {}),
            summary.get("top_rejections", []),
        )
        if summary.get("queued"):
            log.info("Queued-but-not-submitted opportunities: %d", len(summary["queued"]))
        if summary.get("bottleneck"):
            log.warning(summary["bottleneck"])
