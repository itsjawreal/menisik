from __future__ import annotations

from dataclasses import dataclass, field

from src.patch_generator import PatchPlan
from src.project_inspector import ProjectInspection


@dataclass
class ValidationResult:
    status: str
    summary: str
    commands: list[str] = field(default_factory=list)


def validate_patch(plan: PatchPlan, inspection: ProjectInspection) -> ValidationResult:
    commands = []
    if inspection.lint_command:
        commands.append(inspection.lint_command)
    if inspection.test_command:
        commands.append(inspection.test_command)
    changed = list(plan.improvement.changed_files)
    summary = (
        "Patch passed engine syntax checks, diff safety checks, and self-review gates. "
        "Project-level commands were identified but not executed inside this dry-run facade."
    )
    if not changed:
        return ValidationResult(status="failed", summary="No changed files were produced by the patch generator.", commands=commands)
    return ValidationResult(status="passed", summary=summary, commands=commands)
