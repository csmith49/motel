VENV=env
VENV_ACTIVATE=$(VENV)/bin/activate
PYTHON=$(VENV)/bin/python3

env: $(VENV)/bin/activate
$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PYTHON) -m pip install -Ur requirements.txt
	touch $(VENV)/bin/activate

.PRECIOUS: documents/%.db
documents/%.db: data/%.txt env
	$(PYTHON) motel process $< $@

.PRECIOUS: neighborhoods/%.jsonl
neighborhoods/%.jsonl: documents/%.db env
	$(PYTHON) motel extract-neighborhoods $< $@

test: env
	$(PYTHON) motel test