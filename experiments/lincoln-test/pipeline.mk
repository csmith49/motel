# Step 1 - extract neighborhoods from the document
.PRECIOUS: experiments/lincoln-test/neighborhood.jsonl
experiments/lincoln-test/neighborhood.jsonl: data/documents/lincoln-pob.db env
	@$(PYTHON) motel extract-neighborhoods\
		--input experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/neighborhood.jsonl

# Step 2 - synthesize a lot of possible motifs
.PRECIOUS: experiments/lincoln-test/motifs.jsonl
experiments/lincoln-test/motifs.jsonl: experiments/lincoln-test/neighborhood.jsonl mote/enumerate
	@mote/enumerate\
		--input experiments/lincoln-test/neighborhood.jsonl\
		--output experiments/lincoln-test/motifs.jsonl\
		--strategy sample\
		--sample-goal 1000

# Step 3 - evaluate the motifs on just lincoln's data
.PRECIOUS: experiments/lincoln-test/image.jsonl
experiments/lincoln-test/image.jsonl: mote/evaluate experiments/lincoln-test/documents.jsonl experiments/lincoln-test/motifs.jsonl
	@$(PYTHON) motel evaluate-motifs\
		--motifs experiments/lincoln-test/motifs.jsonl\
		--documents experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/image.jsonl

# Step 4 - evaluate ensembles
.PRECIOUS: experiments/lincoln-test/disjunction-performance.jsonl
experiments/lincoln-test/disjunction-performance.jsonl: env experiments/lincoln-test/image.jsonl experiments/lincoln-test/documents.jsonl
	@$(PYTHON) motel evaluate-disjunction\
		--image experiments/lincoln-test/image.jsonl\
		--documents experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/disjunction-performance.jsonl

.PRECIOUS: experiments/lincoln-test/majority-vote-performance.jsonl
experiments/lincoln-test/majority-vote-performance.jsonl: env experiments/lincoln-test/image.jsonl experiments/lincoln-test/documents.jsonl
	@$(PYTHON) motel evaluate-majority-vote\
		--image experiments/lincoln-test/image.jsonl\
		--documents experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/majority-vote-performance.jsonl

.PRECIOUS: experiments/lincoln-test/weighted-vote-performance.jsonl
experiments/lincoln-test/weighted-vote-performance.jsonl: env experiments/lincoln-test/image.jsonl experiments/lincoln-test/documents.jsonl
	@$(PYTHON) motel evaluate-weighted-vote\
		--image experiments/lincoln-test/image.jsonl\
		--documents experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/weighted-vote-performance.jsonl\
		--active-learning-steps 10	