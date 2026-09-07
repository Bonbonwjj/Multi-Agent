from __future__ import annotations

import re
import subprocess
from pathlib import Path

FILE_BLOCK = re.compile(r"```file:([^\n]+)\n(.*?)```", re.DOTALL)
OFFICIAL_BLOCK = re.compile(r"(?m)^([\w./-]+\.[\w]+)\s*\n```[^\n]*\n(.*?)```", re.DOTALL)


def write_file_blocks(text: str, root: Path) -> list[Path]:
    root = root.resolve()
    written: list[Path] = []
    matches = FILE_BLOCK.findall(text) or OFFICIAL_BLOCK.findall(text)
    for name, content in matches:
        target = (root / name.strip()).resolve()
        if root not in target.parents:
            raise ValueError(f"Unsafe generated path: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(target)
    return written


def python_syntax_report(root: Path) -> str:
    failures: list[str] = []
    files = list(root.rglob("*.py"))
    for path in files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            failures.append(f"{path.name}:{exc.lineno}: {exc.msg}")
    if failures:
        return "Syntax failures:\n" + "\n".join(failures)
    return f"Static syntax check passed for {len(files)} Python file(s)."


def execution_report(root: Path, enabled: bool = False, timeout: int = 8) -> str:
    syntax = python_syntax_report(root)
    if "failures" in syntax.lower() or not enabled:
        suffix = " Execution disabled; pass --execute only inside a trusted sandbox." if not enabled else ""
        return syntax + suffix
    candidates = [root / "main.py", root / "task_app.py"]
    entry = next((path for path in candidates if path.exists()), None)
    if entry is None:
        return syntax + " No main.py or task_app.py entrypoint found."
    try:
        completed = subprocess.run(
            ["python3", str(entry)], cwd=root, capture_output=True, text=True, timeout=timeout, input="\n"
        )
    except subprocess.TimeoutExpired:
        return "Runtime timeout: the program did not terminate within the test budget."
    output = (completed.stdout + completed.stderr).strip()
    return f"Exit code: {completed.returncode}\n{output or '(no output)'}"
