.PHONY: test demo chatdev-demo

test:
	PYTHONPATH=src python3 -m pytest -q
	python3 -m compileall -q src examples

demo:
	PYTHONPATH=src python3 examples/reconcile_ceo_group_offline.py

chatdev-demo:
	PYTHONPATH=src python3 -m chatdev_repro.cli --mock --task "开发一个离线待办事项工具" --output outputs/demo
