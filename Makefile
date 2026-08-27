PYTHON ?= python3

.PHONY: all data text entries records networks validate test clean clean-derived

all: validate

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

validate: docs/validation_report.md
docs/validation_report.md: src/validate.py data/processed/network_edges.csv
	$(PYTHON) src/validate.py

## example: descriptive tables and network summaries
example: data/processed/network_edges.csv
	$(PYTHON) examples/quickstart.py

## clean-derived: drop everything rebuildable from the ALTO cache
clean-derived:
	rm -rf data/interim data/processed docs/validation_report.md

## clean: also drop the ~76 MB ALTO cache (forces a re-download)
clean: clean-derived
	rm -rf data/raw

## test: parsing-rule unit tests and dataset integrity checks
.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests -v
