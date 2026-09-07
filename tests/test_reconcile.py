import json

from chatdev_repro.group_agents import Character, GroupAgent
from chatdev_repro.reconcile import AgentGroup, GroupRequest, GroupRoleAgent, ReConcileStrategy
from chatdev_repro.skills import PromptSkill, SkillRegistry


class ReconcileMockLLM:
    def complete(self, messages):
        prompt = messages[-1]["content"]
        agent_id = prompt.split("AGENT_ID=", 1)[1].splitlines()[0]
        reconsider = "MODE=RECONSIDER" in prompt
        answer = "CLI application" if reconsider or agent_id != "user_advocate" else "Desktop application"
        evidence = ["zero third-party dependencies"] if answer == "CLI application" else []
        return json.dumps({
            "answer": answer,
            "claims": ["The product must run offline"],
            "evidence": evidence,
            "uncertainties": [],
            "confidence": 0.9 if evidence else 0.55,
        })


def build_group():
    skill = PromptSkill(
        "product_analysis",
        "Turn requirements into a product definition",
        "Prefer the smallest modality satisfying all constraints.",
        ("extract constraints", "choose modality"),
        required_terms=("application",),
    )
    llm = ReconcileMockLLM()
    agents = [
        GroupAgent("strategist", Character("s", "Strategist", "maximize value"), [skill], llm),
        GroupAgent("user_advocate", Character("u", "User advocate", "protect usability"), [skill], llm),
        GroupAgent("risk_controller", Character("r", "Risk controller", "minimize risk"), [skill], llm),
    ]
    return AgentGroup("ceo_group", "product", agents, ReConcileStrategy(max_rounds=3))


def test_reconcile_reaches_consensus_after_peer_discussion():
    result = build_group().solve(GroupRequest("Build an offline zero-dependency todo tool", "DemandAnalysis"))
    assert result.consensus_answer == "CLI application"
    assert result.confidence == 0.9
    assert len(result.rounds) == 2
    assert result.rounds[0].agreement == 2 / 3
    assert result.rounds[1].agreement == 1.0
    assert set(result.agreements) == {"strategist", "user_advocate", "risk_controller"}
    assert result.evidence == ("zero third-party dependencies",)


def test_skill_registry_and_validation_interface():
    skill = PromptSkill("statistics", "check statistics", "Report uncertainty", required_terms=("confidence",))
    registry = SkillRegistry()
    registry.register(skill)
    assert registry.resolve(["statistics"]) == [skill]
    assert skill.validate("answer without required word") == ["missing required term: confidence"]


def test_group_can_replace_a_legacy_chatdev_role():
    adapter = GroupRoleAgent("ceo", build_group())
    answer = adapter.respond("Choose a modality", [{"role": "user", "content": "offline"}])
    assert answer == "CLI application"
