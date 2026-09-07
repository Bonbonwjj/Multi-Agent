from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SkillContext:
    """Runtime data exposed to a skill when it builds agent instructions."""

    task: str
    phase: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


class Skill(Protocol):
    """Stable extension point for domain knowledge and working procedures."""

    id: str
    description: str

    def instructions(self, context: SkillContext) -> str: ...

    def validate(self, answer: str) -> list[str]: ...


@dataclass(frozen=True)
class PromptSkill:
    """A small in-code skill useful for tests and simple deployments."""

    id: str
    description: str
    knowledge: str
    workflow: tuple[str, ...] = ()
    required_terms: tuple[str, ...] = ()

    def instructions(self, context: SkillContext) -> str:
        steps = "\n".join(f"{index}. {step}" for index, step in enumerate(self.workflow, 1))
        return (
            f"SKILL={self.id}\nScope: {self.description}\nKnowledge:\n{self.knowledge}\n"
            f"Workflow:\n{steps or 'Apply the knowledge directly.'}"
        )

    def validate(self, answer: str) -> list[str]:
        return [f"missing required term: {term}" for term in self.required_terms if term not in answer]


@dataclass(frozen=True)
class MarkdownSkill:
    """Loads a SKILL.md-like file without coupling the framework to Codex."""

    id: str
    description: str
    path: Path

    def instructions(self, context: SkillContext) -> str:
        return self.path.read_text(encoding="utf-8")

    def validate(self, answer: str) -> list[str]:
        return []


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.id in self._skills:
            raise ValueError(f"Skill already registered: {skill.id}")
        self._skills[skill.id] = skill

    def get(self, skill_id: str) -> Skill:
        try:
            return self._skills[skill_id]
        except KeyError as exc:
            raise KeyError(f"Unknown skill: {skill_id}") from exc

    def resolve(self, skill_ids: list[str]) -> list[Skill]:
        return [self.get(skill_id) for skill_id in skill_ids]
