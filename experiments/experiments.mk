# experiments sub-makefile
EXP_FOLDERS=$(shell find experiments -mindepth 1 -type d)
EXP_RESULTS=$(EXP_FOLDERS:%=%/performance.csv)

.PHONY: experiments
experiments: $(EXP_RESULTS)

# General Step 1: extract neighborhoods from training documents
.PRECIOUS: experiments/%/neighborhoods.jsonl
experiments/%/neighborhoods.jsonl: env experiments/%/documents.jsonl
	@echo "Extracting neighborhoods for $*..."
	@$(PYTHON) motel --quiet extract-neighborhoods\
		--input experiments/$*/documents.jsonl\
		--output experiments/$*/neighborhoods.jsonl

# General Step 2: synthesize a whole lot of motifs
.PRECIOUS: experiments/%/motifs.jsonl
experiments/%/motifs.jsonl: mote/enumerate experiments/%/neighborhoods.jsonl
	@echo "Synthesizing motifs for $*..."
	@mote/enumerate\
		--input experiments/$*/neighborhoods.jsonl\
		--output experiments/$*/motifs.jsonl\
		--strategy sample\
		--sample-goal 1500

# General Step 3: evaluate the motifs on the test set
.PRECIOUS: experiments/%/image.jsonl
experiments/%/image.jsonl: env experiments/%/documents.jsonl experiments/%/motifs.jsonl
	@echo "Evaluating motifs for $*..."
	@$(PYTHON) motel evaluate-motifs\
		--motifs experiments/$*/motifs.jsonl\
		--documents experiments/$*/documents.jsonl\
		--output experiments/$*/image.jsonl

# General Step 4: evaluate the resulting ensembles
.PRECIOUS: experiments/%/performance.csv
experiments/%/performance.csv: env experiments/%/image.jsonl experiments/%/documents.jsonl
	@echo "Evaluating ensembles for $*..."
	@$(PYTHON) motel evaluate\
		--image experiments/$*/image.jsonl\
		--documents experiments/$*/documents.jsonl\
		--output experiments/$*/performance.csv\
		--thresholds 5\
		--active-learning-steps 10