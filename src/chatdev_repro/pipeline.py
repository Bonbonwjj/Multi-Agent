from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .agents import Agent, AgentLike, cdh_seminar, seminar
from .config import OFFICIAL_CHAIN, PHASE_GOALS, PhaseSpec
from .events import Event
from .llm import LLM
from .workspace import execution_report, write_file_blocks


@dataclass
class RunResult:
    output_dir: Path
    phases: dict[str, str]
    generated_files: list[Path]
    events: list[Event]


class ChatDevPipeline:
    """Faithful teaching implementation of ChatDev's configurable chat chain."""

    def __init__(
        self,
        llm: LLM,
        turns: int = 2,
        review_rounds: int | None = None,
        execute: bool = False,
        role_executors: dict[str, AgentLike] | None = None,
    ):
        self.llm = llm
        self.turns = turns
        self.review_rounds = review_rounds
        self.execute = execute
        self.role_executors = role_executors or {}

    def _agent(self, role: str) -> AgentLike:
        return self.role_executors.get(role, Agent(role, self.llm))

    @staticmethod
    def _memory(task: str, phases: dict[str, str], report: str = "") -> str:
        # Long-term memory: transmit extracted phase solutions, not every utterance.
        pieces = [f"Customer requirement: {task}"]
        pieces.extend(f"{name}:\n{value}" for name, value in phases.items())
        if report:
            pieces.append(f"Execution report:\n{report}")
        return "\n\n".join(pieces)

    def _run_dialogue(self, spec: PhaseSpec, task: str, context: str):
        pair = (self._agent(spec.instructor), self._agent(spec.assistant))
        request = PHASE_GOALS[spec.name]
        if spec.use_cdh:
            return cdh_seminar(*pair, f"{task}\nSubtask: {request}", spec.name.upper(), context)
        return seminar(*pair, f"{task}\nSubtask: {request}", spec.name.upper(), context, self.turns)

    def run(self, task: str, output_dir: Path) -> RunResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        phases: dict[str, str] = {}
        events: list[Event] = []
        files: list[Path] = []
        report = ""

        for spec in OFFICIAL_CHAIN:
            cycles = self.review_rounds if self.review_rounds is not None and spec.cycles > 1 else spec.cycles
            for cycle in range(1, cycles + 1):
                context = self._memory(task, phases, report)
                result, history = self._run_dialogue(spec, task, context)
                for index, message in enumerate(history):
                    speaker = spec.instructor if message["role"] == "user" else spec.assistant
                    kind = "instruction" if index == 0 else ("clarification" if "<CLARIFY>" in message["content"] else "message")
                    events.append(Event(spec.name, cycle, speaker, kind, message["content"]))
                phases[spec.name] = result
                files.extend(write_file_blocks(result, output_dir))

                if spec.name == "CodeComplete" and "<INFO> Finished" in result:
                    break
                if spec.name == "CodeReview":
                    if "<INFO> Finished" in result:
                        break
                    # Official repo alternates comment and programmer modification.
                    revision, revision_history = cdh_seminar(
                        self._agent("reviewer"), self._agent("programmer"),
                        f"Revise complete code for: {task}", "CODEREVIEWMODIFICATION",
                        self._memory(task, phases),
                    )
                    phases[f"CodeReviewModification{cycle}"] = revision
                    files.extend(write_file_blocks(revision, output_dir))
                    for message in revision_history:
                        speaker = "reviewer" if message["role"] == "user" else "programmer"
                        events.append(Event("CodeReviewModification", cycle, speaker, "message", message["content"]))
                if spec.name == "SystemTest":
                    report = execution_report(output_dir, self.execute)
                    events.append(Event("SystemTest", cycle, "tool", "execution", report))
                    if "Exit code: 0" in report or (not self.execute and "passed" in report.lower()):
                        break

        manifest = {"task": task, "chain": [s.name for s in OFFICIAL_CHAIN], "phases": phases,
                    "events": [event.as_dict() for event in events]}
        (output_dir / "CHATDEV_RUN.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return RunResult(output_dir, phases, sorted(set(files)), events)
