from pathlib import Path

from chatdev_repro.llm import MockLLM
from chatdev_repro.pipeline import ChatDevPipeline
from chatdev_repro.workspace import write_file_blocks


def test_mock_pipeline_generates_runnable_artifacts(tmp_path: Path):
    result = ChatDevPipeline(MockLLM()).run("build a task tracker", tmp_path)
    assert (tmp_path / "task_app.py").exists()
    assert (tmp_path / "CHATDEV_RUN.json").exists()
    assert "DemandAnalysis" in result.phases
    assert "Coding" in result.phases
    assert any(event.kind == "clarification" for event in result.events)
    assert result.phases["LanguageChoose"] == "<INFO> Python"


def test_generated_paths_cannot_escape_workspace(tmp_path: Path):
    try:
        write_file_blocks("```file:../escape.txt\nnope\n```", tmp_path)
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal was accepted")
