from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .llm import LLM
from .skills import Skill, SkillContext


@dataclass(frozen=True)
class Character:
    id: str
    role: str
    goal: str
    traits: tuple[str, ...] = ()
    reasoning_style: str = "evidence-driven"
    communication_style: str = "concise"
    disagreement_policy: str = "state disagreements and request evidence"

    def system_prompt(self) -> str:
        return (
            f"You are {self.role}. Goal: {self.goal}\n"
            f"Traits: {', '.join(self.traits) or 'professional'}\n"
            f"Reasoning style: {self.reasoning_style}\n"
            f"Communication style: {self.communication_style}\n"
            f"When disagreeing: {self.disagreement_policy}"
        )


@dataclass(frozen=True)
class AgentRequest:
    task: str
    phase: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    peer_responses: tuple["AgentResponse", ...] = ()
    round_number: int = 0


@dataclass(frozen=True)
class AgentResponse:
    agent_id: str
    answer: str
    claims: tuple[str, ...]
    evidence: tuple[str, ...]
    uncertainties: tuple[str, ...]
    confidence: float
    round_number: int
    skill_errors: tuple[str, ...] = ()


JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_response(raw: str, agent_id: str, round_number: int) -> AgentResponse:
    match = JSON_BLOCK.search(raw)
    candidate = match.group(1) if match else raw.strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return AgentResponse(agent_id, raw.strip(), (), (), ("unstructured model output",), 0.5, round_number)
    confidence = min(1.0, max(0.0, float(payload.get("confidence", 0.5))))
    return AgentResponse(
        agent_id=agent_id,
        answer=str(payload.get("answer", "")),
        claims=tuple(map(str, payload.get("claims", []))),
        evidence=tuple(map(str, payload.get("evidence", []))),
        uncertainties=tuple(map(str, payload.get("uncertainties", []))),
        confidence=confidence,
        round_number=round_number,
    )


@dataclass
class GroupAgent:
    """An expert agent composed from a character, skills and a model."""

    id: str
    character: Character
    skills: list[Skill]
    llm: LLM

    def act(self, request: AgentRequest) -> AgentResponse:
        skill_context = SkillContext(request.task, request.phase, request.context)
        skill_prompt = "\n\n".join(skill.instructions(skill_context) for skill in self.skills)
        peers = "\n".join(
            f"- {response.agent_id}: {response.answer} (confidence={response.confidence:.2f}; "
            f"evidence={list(response.evidence)})"
            for response in request.peer_responses
            if response.agent_id != self.id
        )
        mode = "INDEPENDENT" if not request.peer_responses else "RECONSIDER"
        prompt = (
            f"MODE={mode}\nAGENT_ID={self.id}\nROUND={request.round_number}\n"
            f"Task: {request.task}\nPhase: {request.phase}\nContext: "
            f"{json.dumps(request.context, ensure_ascii=False, default=str)}\n\n"
            f"Your skills:\n{skill_prompt or 'No specialized skill.'}\n\n"
            f"Peer positions:\n{peers or '(hidden during independent round)'}\n\n"
            "Return JSON only with keys answer, claims, evidence, uncertainties, confidence. "
            "Confidence must be between 0 and 1. In RECONSIDER mode, change your answer only when peer evidence justifies it."
        )
        raw = self.llm.complete([
            {"role": "system", "content": self.character.system_prompt()},
            {"role": "user", "content": prompt},
        ])
        response = _parse_response(raw, self.id, request.round_number)
        errors = tuple(error for skill in self.skills for error in skill.validate(response.answer))
        return AgentResponse(**{**response.__dict__, "skill_errors": errors})
