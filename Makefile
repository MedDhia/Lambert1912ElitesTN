PYTHON ?= python3

.PHONY: all data text entries records networks coding compare validate test figures clean clean-derived

all: validate compare

## data: download the BnF ALTO OCR and the IIIF manifest (cached, resumable)
data:
	$(PYTHON) src/fetch_alto.py

text: data/interim/lines.jsonl
data/interim/lines.jsonl: src/build_text.py
	$(PYTHON) src/build_text.py

entries: data/interim/entries.jsonl
data/interim/entries.jsonl: src/segment_entries.py data/interim/lines.jsonl
	$(PYTHON) src/segment_entries.py

records: data/processed/entries.csv
data/processed/entries.csv: src/extract_records.py data/interim/entries.jsonl
	$(PYTHON) src/extract_records.py

networks: data/processed/network_edges.csv
data/processed/network_edges.csv: src/build_networks.py data/processed/entries.csv
	$(PYTHON) src/build_networks.py

## coding: interpretive layer -- community and gender
coding: data/processed/person_gender.csv
data/processed/person_communities.csv: src/code_communities.py data/processed/network_edges.csv
	$(PYTHON) src/code_communities.py
data/processed/person_gender.csv: src/code_gender.py data/processed/person_communities.csv
	$(PYTHON) src/code_gender.py

## compare: population comparison tables
compare: docs/comparison_tables.md
docs/comparison_tables.md: src/compare_populations.py data/processed/person_gender.csv
	$(PYTHON) src/compare_populations.py > /dev/null

validate: docs/validation_report.md
docs/validation_report.md: src/validate.py data/processed/network_edges.csv
	$(PYTHON) src/validate.py

## example: descriptive tables and network summaries
example: data/processed/network_edges.csv
	$(PYTHON) examples/quickstart.py

## clean-derived: drop everything rebuildable from the ALTO cache
## (source_manifest.json is kept: it is written by the fetch stage, not rebuilt)
clean-derived:
	rm -rf data/interim docs/validation_report.md
	rm -f data/processed/*.csv
	rm -f docs/comparison_tables.md

## clean: also drop the ~76 MB ALTO cache (forces a re-download)
clean: clean-derived
	rm -rf data/raw

## test: parsing-rule unit tests and dataset integrity checks
.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests -v

## figures: render every figure to figures/output/ (needs figures/requirements.txt)
.PHONY: figures
figures:
	cd figures && for f in fig*.py; do $(PYTHON) "$$f"; done
