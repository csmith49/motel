.PRECIOUS: experiments/lincoln-test/neighborhood.jsonl
experiments/lincoln-test/neighborhood.jsonl: data/documents/lincoln-pob.db env
	$(PYTHON) motel extract-neighborhoods data/documents/lincoln-pob.db experiments/lincoln-test/neighborhood.jsonl

# Step 0.2 - synthesize a lot of possible motifs
.PRECIOUS: experiments/lincoln-test/motifs.jsonl
experiments/lincoln-test/motifs.jsonl: experiments/lincoln-test/neighborhood.jsonl mote/enumerate
	mote/enumerate\
		--input experiments/lincoln-test/neighborhood.jsonl\
		--output experiments/lincoln-test/motifs.jsonl\
		--strategy sample\
		--sample-goal 1000

# Step 0.3 - evaluate the motifs on just lincoln's data
.PRECIOUS: experiments/lincoln-test/datasets.jsonl
experiments/lincoln-test/datasets.jsonl:
	@echo "{filename: data/documents/lincoln-pob.db}" > experiments/lincoln-test/datasets.jsonl

.PRECIOUS: experiments/lincoln-test/image.json
experiments/lincoln-test/image.json: mote/evaluate experiments/lincoln-test/datasets.jsonl experiments/lincoln-test/motifs.jsonl
	mote/evaluate\
		--motifs experiments/lincoln-test/motifs.jsonl\
		--data experiments/lincoln-test/datasets.jsonl\
		--output experiments/lincoln-test/image.json
