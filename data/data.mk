# which documents should be made
TXTS=$(shell find data -name "*.txt")
DBS=$(TXTS:data/text/%.txt=data/documents/%.db)

# the phony entrypoint
.PHONY: data
data: $(DBS)

# make a db from a text file
.PRECIOUS: data/documents/%.db
data/documents/%.db: data/text/%.txt env
	@echo "Processing $*..."
	@$(PYTHON) motel --quiet process\
		--input $<\
		--output $@\