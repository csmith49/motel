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
# .PRECIOUS: data/documents/%.db
# data/documents/%.db: data/text/%.txt env
# 	$(PYTHON) motel process\
# 		--input $<\
# 		--output $@

# data generation
include data/data.mk

# experiments
include experiments/experiments.mk

# test rule
.PHONY: test
test: env
	$(PYTHON) motel test