PYTHON ?= python3
CODE := code/pipeline

.PHONY: all data text entries records networks coding compare validate test figures clean clean-derived

all: validate compare measures

## data: download the BnF ALTO OCR and the IIIF manifest (cached, resumable)
data:
	$(PYTHON) $(CODE)/fetch_alto.py

text: data/interim/lines.jsonl
data/interim/lines.jsonl: $(CODE)/build_text.py
	$(PYTHON) $(CODE)/build_text.py

entries: data/interim/entries.jsonl
data/interim/entries.jsonl: $(CODE)/segment_entries.py data/interim/lines.jsonl
	$(PYTHON) $(CODE)/segment_entries.py

records: data/processed/entries.csv
data/processed/entries.csv: $(CODE)/extract_records.py data/interim/entries.jsonl
	$(PYTHON) $(CODE)/extract_records.py

networks: data/processed/network_edges.csv
data/processed/network_edges.csv: $(CODE)/build_networks.py data/processed/entries.csv
	$(PYTHON) $(CODE)/build_networks.py

## coding: interpretive layer -- community and gender
coding: data/processed/person_gender.csv
data/processed/person_communities.csv: $(CODE)/code_communities.py data/processed/network_edges.csv
	$(PYTHON) $(CODE)/code_communities.py
data/processed/person_gender.csv: $(CODE)/code_gender.py data/processed/person_communities.csv
	$(PYTHON) $(CODE)/code_gender.py

## measures: each person's position in the two networks, as dataset columns
measures: data/processed/person_network_measures.csv
data/processed/person_network_measures.csv: $(CODE)/network_measures.py \
		$(CODE)/graph_metrics.py data/processed/network_edges.csv
	$(PYTHON) $(CODE)/network_measures.py

## compare: population comparison tables
compare: output/tables/comparison_tables.md
output/tables/comparison_tables.md: $(CODE)/compare_populations.py \
		$(CODE)/graph_metrics.py data/processed/person_gender.csv
	$(PYTHON) $(CODE)/compare_populations.py > /dev/null

validate: docs/validation_report.md
docs/validation_report.md: $(CODE)/validate.py data/processed/network_edges.csv
	$(PYTHON) $(CODE)/validate.py

## example: descriptive tables and network summaries
example: data/processed/network_edges.csv
	$(PYTHON) code/examples/quickstart.py

## clean-derived: drop everything rebuildable from the ALTO cache
## (source_manifest.json is kept: it is written by the fetch stage, not rebuilt)
clean-derived:
	rm -rf data/interim docs/validation_report.md
	rm -f data/processed/*.csv
	rm -f output/tables/comparison_tables.md

## clean: also drop the ~76 MB ALTO cache (forces a re-download)
clean: clean-derived
	rm -rf data/raw

## test: parsing-rule unit tests and dataset integrity checks
.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests -v

## figures: render every figure to output/figures/ (needs requirements.txt)
.PHONY: figures
figures:
	cd code/figures && for f in fig*.py; do $(PYTHON) "$$f"; done
