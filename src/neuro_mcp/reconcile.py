from __future__ import annotations

from collections import defaultdict

from .models import Mode, ReconcileReport, SearchResult
from .text_utils import tokenize


def reconcile_results(
    query: str,
    brain_results: list[SearchResult],
    code_results: list[SearchResult],
    manifests: dict[str, set[str]],
    mode: Mode,
) -> ReconcileReport:
    contradictions: list[str] = []
    recommendations: list[str] = []

    query_tokens = set(tokenize(query))
    actual_dependencies = set()
    for deps in manifests.values():
        actual_dependencies.update(dep.lower() for dep in deps)

    for brain in brain_results:
        claimed = {dep.lower() for dep in brain.metadata.get("claimed_dependencies", [])}
        missing_claims = sorted(dep for dep in claimed if dep not in actual_dependencies)
        if missing_claims:
            message = (
                f"Note '{brain.title}' claims dependencies missing from manifests: "
                + ", ".join(missing_claims)
            )
            contradictions.append(message)
            brain.contradictions.append(message)

        if not brain.source_files_exist:
            message = f"Note '{brain.title}' references source files that do not exist."
            contradictions.append(message)
            brain.contradictions.append(message)

        if brain.freshness in {"stale", "missing_sources"}:
            message = f"Note '{brain.title}' is {brain.freshness}."
            contradictions.append(message)
            brain.contradictions.append(message)

    if contradictions:
        source_of_truth = "code"
        recommendations.append("Treat codebase results as source of truth and mark conflicting notes as labile or stale.")
    else:
        source_of_truth = "brain+code"
        recommendations.append("No explicit contradiction detected. Use brain for rationale and code for implementation detail.")

    # Query-specific recommendation.
    if query_tokens & {"architecture", "adr", "decision"}:
        recommendations.append("Prefer CA3-style stable notes first, then verify with code.")
    if query_tokens & {"bug", "fix", "sprint", "todo"}:
        recommendations.append("Prefer CA1-style fresh notes and recent code changes first.")

    return ReconcileReport(
        query=query,
        source_of_truth=source_of_truth,
        mode=mode,
        brain_results=brain_results,
        code_results=code_results,
        contradictions=contradictions,
        recommendations=recommendations,
    )
