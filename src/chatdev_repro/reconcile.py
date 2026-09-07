from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .group_agents import AgentRequest, AgentResponse, GroupAgent


@dataclass(frozen=True)
class GroupRequest:
    task: str
    phase: str = ""
    context: dict[str, object] | None = None


@dataclass(frozen=True)
class ReconcileRound:
    number: int
    responses: tuple[AgentResponse, ...]
    agreement: float


@dataclass(frozen=True)
class GroupResponse:
    group_id: str
    consensus_answer: str
    confidence: float
    agreements: tuple[str, ...]
    disagreements: tuple[str, ...]
    evidence: tuple[str, ...]
    rounds: tuple[ReconcileRound, ...]


class CollaborationStrategy(Protocol):
    def run(self, group_id: str, agents: list[GroupAgent], request: GroupRequest) -> GroupResponse: ...


def _normalized(answer: str) -> str:
    return " ".join(answer.lower().split())


def _agreement(responses: tuple[AgentResponse, ...]) -> float:
    if not responses:
        return 0.0
    counts: dict[str, int] = {}
    for response in responses:
        key = _normalized(response.answer)
        counts[key] = counts.get(key, 0) + 1
    return max(counts.values()) / len(responses)


@dataclass
class EvidenceWeightedAggregator:
    evidence_bonus: float = 0.08
    skill_error_penalty: float = 0.15

    def aggregate(self, group_id: str, rounds: list[ReconcileRound]) -> GroupResponse:
        final = rounds[-1].responses
        buckets: dict[str, list[AgentResponse]] = {}
        for response in final:
            buckets.setdefault(_normalized(response.answer), []).append(response)

        def score(item: tuple[str, list[AgentResponse]]) -> float:
            _, members = item
            return sum(
                member.confidence
                + self.evidence_bonus * min(3, len(member.evidence))
                - self.skill_error_penalty * len(member.skill_errors)
                for member in members
            )

        winning_key, winners = max(buckets.items(), key=score)
        consensus = max(winners, key=lambda response: response.confidence).answer
        agreements = tuple(response.agent_id for response in winners)
        disagreements = tuple(
            f"{response.agent_id}: {response.answer}" for response in final if _normalized(response.answer) != winning_key
        )
        evidence = tuple(dict.fromkeys(item for response in winners for item in response.evidence))
        confidence = sum(response.confidence for response in winners) / len(winners)
        return GroupResponse(group_id, consensus, confidence, agreements, disagreements, evidence, tuple(rounds))


@dataclass
class ReConcileStrategy:
    """Independent answers followed by evidence-aware peer reconsideration."""

    max_rounds: int = 3
    consensus_threshold: float = 0.75
    aggregator: EvidenceWeightedAggregator = field(default_factory=EvidenceWeightedAggregator)

    def run(self, group_id: str, agents: list[GroupAgent], request: GroupRequest) -> GroupResponse:
        if not agents:
            raise ValueError("An AgentGroup requires at least one agent")
        context = request.context or {}
        rounds: list[ReconcileRound] = []
        responses = tuple(
            agent.act(AgentRequest(request.task, request.phase, context, round_number=0)) for agent in agents
        )
        rounds.append(ReconcileRound(0, responses, _agreement(responses)))

        for number in range(1, self.max_rounds):
            if rounds[-1].agreement >= self.consensus_threshold:
                break
            responses = tuple(
                agent.act(AgentRequest(request.task, request.phase, context, responses, number)) for agent in agents
            )
            rounds.append(ReconcileRound(number, responses, _agreement(responses)))
        return self.aggregator.aggregate(group_id, rounds)


@dataclass
class AgentGroup:
    id: str
    domain: str
    agents: list[GroupAgent]
    strategy: CollaborationStrategy

    def solve(self, request: GroupRequest) -> GroupResponse:
        return self.strategy.run(self.id, self.agents, request)


@dataclass
class GroupRoleAgent:
    """Adapter that lets an AgentGroup occupy any legacy ChatDev role slot."""

    role: str
    group: AgentGroup

    def respond(self, prompt: str, history: list[dict[str, str]] | None = None) -> str:
        context = {"history": history or []}
        result = self.group.solve(GroupRequest(prompt, phase=self.role, context=context))
        return result.consensus_answer
