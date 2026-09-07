from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .llm import LLM


ROLES = {
    "ceo": "You are the CEO. Clarify product goals and user value.",
    "product": "You are the Chief Product Officer. Turn customer needs into a realizable product definition and manual.",
    "cto": "You are the CTO. Make concrete architecture and technology decisions.",
    "programmer": "You are the programmer. Return complete code using ```file:path blocks.",
    "reviewer": "You are the code reviewer. Find defects and demand precise fixes.",
    "tester": "You are the tester. Derive tests from requirements and report failures precisely.",
    "writer": "You are the technical writer. Produce concise usage documentation.",
}


class AgentLike(Protocol):
    role: str

    def respond(self, prompt: str, history: list[dict[str, str]] | None = None) -> str: ...


@dataclass
class Agent:
    role: str
    llm: LLM

    def respond(self, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        messages = [{"role": "system", "content": ROLES[self.role]}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": prompt})
        return self.llm.complete(messages)


def seminar(
    instructor: AgentLike,
    assistant: AgentLike,
    task: str,
    phase: str,
    context: str = "",
    turns: int = 2,
) -> tuple[str, list[dict[str, str]]]:
    """Role-playing dialogue with ChatDev's request-response dehallucination loop."""
    history: list[dict[str, str]] = []
    instruction = (
        f"PHASE={phase}\nTask: {task}\nPrior artifacts:\n{context}\n"
        "Give a concrete solution. If information is missing, ask one explicit question."
    )
    answer = assistant.respond(instruction)
    history += [{"role": "user", "content": instruction}, {"role": "assistant", "content": answer}]
    for _ in range(max(0, turns - 1)):
        followup = instructor.respond(
            "Inspect the assistant's result. Resolve ambiguity by asking for a concrete correction; "
            "if complete, say what final artifact must be returned.",
            history,
        )
        history.append({"role": "user", "content": followup})
        answer = assistant.respond(
            "Apply the instructor's request now. Return the complete revised artifact, not commentary.",
            history,
        )
        history.append({"role": "assistant", "content": answer})
    return answer, history


def cdh_seminar(
    instructor: AgentLike,
    assistant: AgentLike,
    task: str,
    phase: str,
    context: str,
) -> tuple[str, list[dict[str, str]]]:
    """Paper Eq. 7: instruction → clarification → detail → final solution."""
    instruction = f"PHASE={phase}\nTask: {task}\nArtifacts:\n{context}"
    clarification = assistant.respond(
        instruction
        + "\nBefore the formal solution, identify the single most consequential ambiguity or likely defect and ask for one precise suggestion. Prefix it <CLARIFY>."
    )
    detail = instructor.respond(
        "Give one concrete, actionable detail that resolves this request. Do not solve the whole task yet.",
        [{"role": "user", "content": instruction}, {"role": "assistant", "content": clarification}],
    )
    history = [
        {"role": "user", "content": instruction},
        {"role": "assistant", "content": clarification},
        {"role": "user", "content": detail},
    ]
    answer = assistant.respond(
        "Now use that detail to deliver the complete formal result. Follow the requested output contract.", history
    )
    history.append({"role": "assistant", "content": answer})
    return answer, history
