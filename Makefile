.PHONY: test test-deps test-one

test-deps:
	venv/bin/pip install -r requirements-test.txt

test: test-deps
	PYTHONPATH=. venv/bin/pytest tests/ -v

test-one: test-deps
	PYTHONPATH=. venv/bin/pytest $(TEST) -v -s