# Group-Agent / ReConcile extension

The extension keeps the original `Agent(role, llm)` API while allowing any role slot to be replaced by an `AgentGroup`.

## Interfaces

```python
class Skill(Protocol):
    id: str
    description: str
    def instructions(self, context: SkillContext) -> str: ...
    def validate(self, answer: str) -> list[str]: ...

@dataclass
class GroupAgent:
    id: str
    character: Character
    skills: list[Skill]
    llm: LLM
    def act(self, request: AgentRequest) -> AgentResponse: ...

@dataclass
class AgentGroup:
    id: str
    domain: str
    agents: list[GroupAgent]
    strategy: CollaborationStrategy
    def solve(self, request: GroupRequest) -> GroupResponse: ...
```

## ReConcile flow

```text
round 0: each member answers independently
    ↓ agreement below threshold
round 1..N: members see peer answers, evidence and confidence
    ↓
evidence-weighted aggregation
    ↓
consensus + agreements + disagreements + evidence + full rounds
```

## Replace CEO with a group

```python
ceo_group = AgentGroup(
    id="ceo_group",
    domain="product",
    agents=[strategist, user_advocate, risk_controller],
    strategy=ReConcileStrategy(max_rounds=3),
)

pipeline = ChatDevPipeline(
    llm=llm,
    role_executors={"ceo": GroupRoleAgent("ceo", ceo_group)},
)
pipeline.run("Build an offline task manager", Path("outputs/group-demo"))
```

The same bridge works for `cto`, `programmer`, `reviewer`, `tester`, or any future role. A group owns its member models and skills; the surrounding ChatDev phase remains unchanged.

## Skill implementations

- `PromptSkill`: knowledge and workflow declared directly in Python.
- `MarkdownSkill`: load instructions from a local Markdown file.
- `SkillRegistry`: register skills once and resolve them by ID.

A future tool-backed skill can implement the same `Skill` protocol without changing `GroupAgent` or ReConcile.
