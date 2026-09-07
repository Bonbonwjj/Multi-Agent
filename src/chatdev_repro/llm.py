from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLM(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


@dataclass
class OpenAICompatibleLLM:
    """Minimal dependency-free client for OpenAI-compatible chat endpoints."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout: int = 120

    @classmethod
    def from_env(cls) -> "OpenAICompatibleLLM":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OPENAI_API_KEY is required (or run with --mock).")
        return cls(
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )

    def complete(self, messages: list[dict[str, str]]) -> str:
        body = json.dumps({"model": self.model, "messages": messages, "temperature": 0.2}).encode()
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"LLM request failed ({exc.code}): {detail}") from exc
        return payload["choices"][0]["message"]["content"]


class MockLLM:
    """Deterministic backend for smoke tests and understanding the workflow."""

    def complete(self, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"]
        role_prompt = messages[0]["content"]
        if "<CLARIFY>" in prompt or "Before the formal solution" in prompt:
            return "<CLARIFY> Which single acceptance criterion or concrete defect should I prioritize?"
        joined = "\n".join(message["content"] for message in messages)
        if "DEMANDANALYSIS" in joined:
            return "<INFO> Application"
        if "LANGUAGECHOOSE" in joined:
            return "<INFO> Python"
        if "PHASE=DESIGN" in prompt:
            return (
                "Product: a small command-line task tracker.\n"
                "Architecture: Python standard library, JSON persistence, argparse CLI.\n"
                "Acceptance: add/list/done commands; readable errors; unit tests."
            )
        if "ENVIRONMENTDOC" in joined:
            return "```file:requirements.txt\n# Python standard library only\n```"
        if "MANUAL" in joined or "product officer" in role_prompt.lower():
            return "```file:manual.md\n# Generated task tracker\nUse `python task_app.py list`.\n```"
        if "CODING" in joined or "CODEREVIEWMODIFICATION" in joined or "SYSTEMTEST" in joined or "programmer" in role_prompt.lower():
            return '''```file:task_app.py
import argparse
import json
from pathlib import Path

def load(path):
    return json.loads(path.read_text()) if path.exists() else []

def save(path, tasks):
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["add", "list", "done"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--db", default="tasks.json")
    args = parser.parse_args(argv)
    path, tasks = Path(args.db), load(Path(args.db))
    if args.command == "add":
        if not args.value: parser.error("add requires a task")
        tasks.append({"text": args.value, "done": False}); save(path, tasks)
    elif args.command == "done":
        if args.value is None or not args.value.isdigit(): parser.error("done requires an index")
        tasks[int(args.value)]["done"] = True; save(path, tasks)
    else:
        for i, task in enumerate(tasks): print(f"{i}: [{'x' if task['done'] else ' '}] {task['text']}")

if __name__ == "__main__": main()
```
```file:README.md
# Generated task tracker
Run `python task_app.py add "write tests"`, then `python task_app.py list`.
```'''
        if "PHASE=TEST" in prompt or "tester" in role_prompt.lower() or "reviewer" in role_prompt.lower():
            return "Check CLI parsing, persistence, empty database, and invalid indexes."
        if "PHASE=DOCUMENT" in prompt or "technical writer" in role_prompt.lower():
            return "The generated program is a dependency-free task tracker; see its README for usage."
        return "Please provide the concrete artifact and finish with a decisive result."
