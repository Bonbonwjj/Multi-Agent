from __future__ import annotations

import argparse
from pathlib import Path

from .llm import MockLLM, OpenAICompatibleLLM
from .pipeline import ChatDevPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compact ChatDev paper reproduction")
    parser.add_argument("--task", required=True, help="software requirement in natural language")
    parser.add_argument("--output", default="outputs/demo")
    parser.add_argument("--turns", type=int, default=2)
    parser.add_argument("--review-rounds", type=int, default=1)
    parser.add_argument("--execute", action="store_true", help="execute generated code (trusted sandbox only)")
    parser.add_argument("--mock", action="store_true", help="run offline deterministic demo")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    llm = MockLLM() if args.mock else OpenAICompatibleLLM.from_env()
    result = ChatDevPipeline(llm, args.turns, args.review_rounds, args.execute).run(args.task, Path(args.output))
    print(f"Finished: {result.output_dir}")
    for path in result.generated_files:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
