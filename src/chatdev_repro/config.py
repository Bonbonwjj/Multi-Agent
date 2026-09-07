from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseSpec:
    name: str
    instructor: str
    assistant: str
    cycles: int = 1
    use_cdh: bool = False


# Mirrors the paper's three phases/five core subtasks and the chatdev1.0
# implementation's document-producing tail.
OFFICIAL_CHAIN = (
    PhaseSpec("DemandAnalysis", "ceo", "product", use_cdh=True),
    PhaseSpec("LanguageChoose", "ceo", "cto", use_cdh=True),
    PhaseSpec("Coding", "cto", "programmer"),
    PhaseSpec("CodeComplete", "cto", "programmer", cycles=10, use_cdh=True),
    PhaseSpec("CodeReview", "programmer", "reviewer", cycles=3, use_cdh=True),
    PhaseSpec("SystemTest", "tester", "programmer", cycles=3, use_cdh=True),
    PhaseSpec("EnvironmentDoc", "cto", "programmer", use_cdh=True),
    PhaseSpec("Manual", "ceo", "product"),
)


PHASE_GOALS = {
    "DemandAnalysis": "Choose one realizable product modality. End with <INFO> modality.",
    "LanguageChoose": "Choose one concrete programming language. Prefer Python when suitable. End with <INFO> language.",
    "Coding": "Write a fully functional multi-file implementation. Return complete files in ```file:path blocks; no pass or TODO.",
    "CodeComplete": "Inspect all code for missing files, imports, classes and unimplemented methods. Return <INFO> Finished or complete revised files.",
    "CodeReview": "Check imports, implementations, logic, requirement coverage and interaction. Return only the highest-priority issue or <INFO> Finished.",
    "SystemTest": "Use the execution report to locate the concrete bug. Return <INFO> Finished if it passes, otherwise complete corrected files.",
    "EnvironmentDoc": "Produce requirements.txt in a file block containing the exact dependencies implied by the code.",
    "Manual": "Produce manual.md in a file block with features, installation and usage.",
}
