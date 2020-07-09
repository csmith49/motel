SOTONE=experiments/start-of-term-one

# Step 1 - extract neighborhoods from the training documents
.PRECIOUS: $(SOTONE)/neighborhood.jsonl
$(SOTONE)/neighborhood.jsonl: env $(SOTONE)/documents.jsonl
	@$(PYTHON) motel extract-neighborhoods\
		--input $(SOTONE)/documents.jsonl\
		--output $(SOTONE)/neighborhood.jsonl

# Step 2 - synthesize a lot of possible motifs
.PRECIOUS: $(SOTONE)/motifs.jsonl
$(SOTONE)/motifs.jsonl: $(SOTONE)/neighborhood.jsonl mote/enumerate
	@mote/enumerate\
		--input $(SOTONE)/neighborhood.jsonl\
		--output $(SOTONE)/motifs.jsonl\
		--strategy sample\
		--sample-goal 1000

# Step 3 - evaluate the motifs
.PRECIOUS: $(SOTONE)/image.jsonl
$(SOTONE)/image.jsonl: mote/evaluate $(SOTONE)/documents.jsonl $(SOTONE)/motifs.jsonl
	@$(PYTHON) motel evaluate-motifs\
		--motifs $(SOTONE)/motifs.jsonl\
		--documents $(SOTONE)/documents.jsonl\
		--output $(SOTONE)/image.jsonl

# Step 4 - evaluate ensembles
.PRECIOUS: $(SOTONE)/disjunction-performance.jsonl
$(SOTONE)/disjunction-performance.jsonl: env $(SOTONE)/image.jsonl $(SOTONE)/documents.jsonl
	@$(PYTHON) motel evaluate-disjunction\
		--image $(SOTONE)/image.jsonl\
		--documents $(SOTONE)/documents.jsonl\
		--output $(SOTONE)/disjunction-performance.jsonl

.PRECIOUS: $(SOTONE)/majority-vote-performance.jsonl
$(SOTONE)/majority-vote-performance.jsonl: env $(SOTONE)/image.jsonl $(SOTONE)/documents.jsonl
	@$(PYTHON) motel evaluate-majority-vote\
		--image $(SOTONE)/image.jsonl\
		--documents $(SOTONE)/documents.jsonl\
		--output $(SOTONE)/majority-vote-performance.jsonl

.PRECIOUS: $(SOTONE)/weighted-vote-performance.jsonl
$(SOTONE)/weighted-vote-performance.jsonl: env $(SOTONE)/image.jsonl $(SOTONE)/documents.jsonl
	@$(PYTHON) motel evaluate-weighted-vote\
		--image $(SOTONE)/image.jsonl\
		--documents $(SOTONE)/documents.jsonl\
		--output $(SOTONE)/weighted-vote-performance.jsonl\
		--active-learning-steps 10	