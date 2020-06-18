# virtual environment as a rule means python dependencies always up to date
VENV=env
VENV_ACTIVATE=$(VENV)/bin/activate
PYTHON=$(VENV)/bin/python3

env: $(VENV)/bin/activate
$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PYTHON) -m pip install -Ur requirements.txt
	touch $(VENV)/bin/activate

# submodule rules
mote: mote/README.md
mote/README.md:
	git submodule update --init --recursive
mote/enumerate mote/evaluate: mote mote/bin/enumerate.ml mote/bin/evaluate.ml
	$(MAKE) -C mote

# making documents from text
.PRECIOUS: data/documents/%.db
data/documents/%.db: data/text/%.txt env
	$(PYTHON) motel process $< $@

# EXPERIMENTS
include experiments/experiments.mk

#temp rule
evaluate: env data/documents/lincoln-pob.db
	$(PYTHON) motel evaluate experiments/lincoln-test/motifs.jsonl data/documents/lincoln-pob.db

# test rule
.PHONY: test
test: env
	$(PYTHON) motel test

# temp test rule
analyze: env
	$(PYTHON) motel analyze-image abc def