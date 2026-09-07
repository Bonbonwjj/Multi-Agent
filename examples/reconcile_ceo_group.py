from __future__ import annotations

import json

from chatdev_repro.group_agents import Character, GroupAgent
from chatdev_repro.llm import OpenAICompatibleLLM
from chatdev_repro.reconcile import AgentGroup, GroupRequest, ReConcileStrategy
from chatdev_repro.skills import PromptSkill


def build_group(llm: OpenAICompatibleLLM) -> AgentGroup:
    product = PromptSkill(
        id="product_analysis",
        description="Convert user needs into a realizable product definition.",
        knowledge="Prioritize users, constraints, acceptance criteria and minimum viable scope.",
        workflow=("Identify the target user", "Extract constraints", "Propose measurable acceptance criteria"),
    )
    agents = [
        GroupAgent("strategist", Character("strategist", "Product strategist", "maximize product value", ("decisive",)), [product], llm),
        GroupAgent("user_advocate", Character("advocate", "User advocate", "protect user needs", ("empathetic",)), [product], llm),
        GroupAgent("risk_controller", Character("risk", "Risk controller", "minimize delivery risk", ("skeptical",)), [product], llm),
    ]
    return AgentGroup("ceo_group", "product", agents, ReConcileStrategy(max_rounds=3))


if __name__ == "__main__":
    group = build_group(OpenAICompatibleLLM.from_env())
    result = group.solve(GroupRequest("设计一个离线学生成绩管理工具", "DemandAnalysis"))
    print(json.dumps(result, default=lambda value: value.__dict__, ensure_ascii=False, indent=2))
