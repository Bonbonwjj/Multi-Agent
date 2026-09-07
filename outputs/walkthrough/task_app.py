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
