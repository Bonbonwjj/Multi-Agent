"""Offline, deterministic ReConcile demonstration requiring no API key."""

from __future__ import annotations

import json

from chatdev_repro.group_agents import Character, GroupAgent
from chatdev_repro.reconcile import AgentGroup, GroupRequest, ReConcileStrategy
from chatdev_repro.skills import PromptSkill


class DemoLLM:
    def complete(self, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"]
        agent_id = prompt.split("AGENT_ID=", 1)[1].splitlines()[0]
        reconsider = "MODE=RECONSIDER" in prompt
        cli = reconsider or agent_id != "user_advocate"
        return json.dumps(
            {
                "answer": "CLI application" if cli else "Desktop application",
                "claims": ["The product must work offline without third-party packages"],
                "evidence": ["Python standard library provides argparse and json"] if cli else [],
                "uncertainties": [] if cli else ["GUI increases delivery cost"],
                "confidence": 0.92 if cli else 0.55,
            }
        )


def build_ceo_group() -> AgentGroup:
    skill = PromptSkill(
        id="product_analysis",
        description="Convert customer needs into a realizable product definition.",
        knowledge="Prefer the smallest product modality that satisfies every hard constraint.",
        workflow=("extract constraints", "compare modalities", "state acceptance criteria"),
        required_terms=("application",),
    )
    llm = DemoLLM()
    members = [
        GroupAgent("strategist", Character("strategist", "Product strategist", "maximize product value"), [skill], llm),
        GroupAgent("user_advocate", Character("advocate", "User advocate", "protect usability"), [skill], llm),
        GroupAgent("risk_controller", Character("risk", "Risk controller", "minimize delivery risk"), [skill], llm),
    ]
    return AgentGroup("ceo_group", "product", members, ReConcileStrategy(max_rounds=3))


if __name__ == "__main__":
    result = build_ceo_group().solve(
        GroupRequest(
            "Build an offline task manager with JSON persistence and no third-party dependencies",
            "DemandAnalysis",
        )
    )
    print(f"Consensus: {result.consensus_answer}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Rounds: {len(result.rounds)}")
    print(f"Agreement: {', '.join(result.agreements)}")
    print(f"Evidence: {'; '.join(result.evidence)}")
