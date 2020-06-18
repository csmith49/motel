# Step 1 - extract neighborhoods from the document
.PRECIOUS: experiments/lincoln-test/neighborhood.jsonl
experiments/lincoln-test/neighborhood.jsonl: data/documents/lincoln-pob.db env
	$(PYTHON) motel extract-neighborhoods\
		--input data/documents/lincoln-pob.db\
		--output experiments/lincoln-test/neighborhood.jsonl

# Step 2 - synthesize a lot of possible motifs
.PRECIOUS: experiments/lincoln-test/motifs.jsonl
experiments/lincoln-test/motifs.jsonl: experiments/lincoln-test/neighborhood.jsonl mote/enumerate
	mote/enumerate\
		--input experiments/lincoln-test/neighborhood.jsonl\
		--output experiments/lincoln-test/motifs.jsonl\
		--strategy sample\
		--sample-goal 1000

# Step 3 - evaluate the motifs on just lincoln's data
.PRECIOUS: experiments/lincoln-test/datasets.jsonl
experiments/lincoln-test/documents.jsonl:
	@echo '{"filename": "data/documents/lincoln-pob.db"}' > experiments/lincoln-test/documents.jsonl

.PRECIOUS: experiments/lincoln-test/image.json
experiments/lincoln-test/image.jsonl: mote/evaluate experiments/lincoln-test/documents.jsonl experiments/lincoln-test/motifs.jsonl
	$(PYTHON) motel evaluate\
		--motifs experiments/lincoln-test/motifs.jsonl\
		--documents experiments/lincoln-test/documents.jsonl\
		--output experiments/lincoln-test/image.jsonl
