from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Event:
    phase: str
    cycle: int
    speaker: str
    kind: str
    content: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
