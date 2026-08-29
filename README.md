# Lambert 1912: a dataset of the colonial elite of Tunisia

A machine-readable dataset built from Paul Lambert, *Dictionnaire illustré de la
Tunisie: choses et gens de Tunisie* (Tunis: C. Saliba aîné, 1912) — a 468-page
illustrated who's-who and gazetteer of the French Protectorate, published three
decades after the Treaty of Bardo.

The volume is a self-portrait of a colonial elite: 1,300-odd biographical
notices written to a fixed template, alongside notices on the localities, the
associations, and the vocabulary of the Regency. That template is what makes it
codeable. This repository turns it into tables a social scientist can use —
individual attributes, career sequences, state honours, and the affiliation ties
that connect people to associations, public bodies, and places.

**Source**: BnF/Gallica, [ark:/12148/bpt6k5505300s](https://gallica.bnf.fr/ark:/12148/bpt6k5505300s),
494 views, public domain. Text obtained from Gallica's documented ALTO OCR
service; no page is scraped from the reading interface.

## What is in it

| | n |
|---|---|
| Dictionary entries segmented | 2,741 |
| Biographical notices (persons) | 1,307 |
| Localities | 736 |
| Associations and public bodies | 159 |
| Arabic/Tunisian terms and other topics | 470 |
| Cross-references | 69 |
| Honours coded (person × order) | 1,810 |
| Career posts | 1,449 |
| Educational institutions attended | 1,158 |
| Affiliation ties (person → organisation) | 1,761 |
| Person → place ties (birth, residence, property) | 2,104 |
| Network nodes / edges | 4,008 / 3,865 |
| Persons with a coded community | 802 of 1,307 |
| Persons placed as colonist or native | 830 of 1,307 (704 / 126) |
| Persons with a coded gender | 1,126 of 1,307 (11 women) |
| Person nodes with network measures | 1,134 (556 with a notice) |

Lambert's preface states his own totals — "more than 1,300" biographies, "more
than 750" localities, "more than 175" societies, 420 portraits. The pipeline
never sees those figures, so they serve as an independent check: it recovers
101%, 98%, 91% and 100% of them. The two shortfalls are real and are not
smoothed over — some locality and association notices are absorbed into the
entry above when OCR loses the first-line indent, so those two tables are
high-precision but incomplete. See
[`docs/validation_report.md`](docs/validation_report.md).

Files live in `data/processed/`; every variable is defined in
[`docs/codebook.md`](docs/codebook.md); the method is documented in
[`docs/provenance.md`](docs/provenance.md).

## What it is good for

The volume was compiled at a particular moment — months after the Jellaz affair
of November 1911 and in the year of the tram boycott, as the Young Tunisian
movement mounted the Protectorate's first organised nationalist challenge — and
it records the settler and administrative elite as it wished to be seen. That
makes it usable for questions such as:

- **Elite composition and recruitment.** Birth cohorts, birthplaces (metropolitan
  France, Algeria, Corsica, Italy, Malta, Tunisia), education, and the sectoral
  distribution of an imperial administrative class.
- **State recognition as a resource.** Two honours systems operate side by side:
  the French Légion d'honneur and Palmes académiques, and the Bey's Nichan
  Iftikhar. Who accumulates which, and in what grade, is a direct measure of
  how each authority distributed status — and 707 of 1,307 people carry a
  beylical honour against 178 with the Légion d'honneur.
- **Associational life as social structure.** The affiliation network links
  people to mutual-aid societies, chambers of commerce and agriculture, learned
  societies, sporting clubs, masonic lodges, and national-community associations
  — the institutional fabric of settler society, with roles attached.
- **Career sequences.** `career_positions.csv` preserves the printed order of
  posts, so trajectories (military → administration, metropole → colony →
  Protectorate) can be modelled as sequences.
- **Colonial space.** Localities carry both administrative geographies —
  *contrôle civil* and *caïdat* — plus infrastructure mentions and named
  landowners, which link individuals to specific rural properties.
- **Network position as a variable.** `person_network_measures.csv` gives each
  person's degree, betweenness, closeness and clustering in both the two-mode
  affiliation network and its one-mode projection, with the component they sit
  in, so structure can go straight into a model without rebuilding the graph.
- **The volume as an object of study.** Entry length, portrait presence, and the
  editorial rubrics are measures of the compiler's own hierarchy of attention.
- **Comparing the communities the Protectorate governed separately.**
  `person_communities.csv` codes each notice as European (French, Italian,
  Maltese, other) or Tunisian (Muslim, Jewish) from the institutional,
  educational and birthplace evidence in the entry itself — never from a
  surname. `person_gender.csv` does the same for gender. Both keep their
  evidence and a confidence on every row, and both leave silence as silence.
  See [`output/tables/comparison_tables.md`](output/tables/comparison_tables.md).
- **Position in the colonial order.** `person_positionality.csv` re-reads the
  same evidence on a different axis: `colonist` (European-origin, metropolitan
  or settler) against `native` (Tunisian-origin, Muslim and Jewish alike, which
  is the volume's own usage). It carries `position_detail` for the intermediary
  cases — colony-born settlers, and the Grana, Jews with Italian nationality —
  and `position_basis` for *how* each person was placed. That last column is not
  bookkeeping: natives are mostly identified through a communal institution and
  colonists through a birthplace, and institutional ties are also what put a
  person in the network, so any comparison that does not hold the basis constant
  measures the coding rather than the elite. A third of the volume stays
  unplaced, and asymmetrically so — the native count is a floor.

## What it is not

It is not a census, a sample, or a population register. Inclusion was decided in
1912 by a Tunis publisher, and the selection is heavily French, urban, male, and
propertied. Tunisian Muslims and Jews appear mainly as notables, officials, and
merchants; women are almost absent. Ties are undated and cross-sectional. Read
the limitations section of the validation report before treating any count as a
population quantity — the dataset is evidence about a colonial elite's
self-representation, and is most defensible when used as such.

Nor is the transcription perfect. The volume is set in two columns and the OCR
occasionally runs one notice into the next: 33 entries of 2,741 carry two or
three people's text under the first one's name, so attributes read out of the
tail of an entry can belong to the following person. The effect is small and
detectable — a notice header is a recognisable string — but it is real, and it
was large enough to produce a false finding before it was caught. Anything
derived from the free text of a long entry deserves a glance at the page.

## Layout

All code lives under `code/`, everything a script generates under `output/`.

```
code/pipeline/            the pipeline, each stage runnable on its own
  fetch_alto.py           download the BnF ALTO OCR and IIIF manifest (cached)
  build_text.py           ALTO -> column-aware, de-hyphenated line stream
  segment_entries.py      line stream -> dictionary entries
  extract_records.py      entries -> typed records and variables
  build_networks.py       records -> mentions, ties, nodes and edges
  code_communities.py     interpretive layer: European / Tunisian community
  code_gender.py          interpretive layer: gender
  code_positionality.py   interpretive layer: colonist / native position
  graph_metrics.py        centrality in pure Python (no dependencies)
  network_measures.py     -> data/processed/person_network_measures.csv
  compare_populations.py  -> output/tables/comparison_tables.md
  validate.py             -> docs/validation_report.md
code/figures/             63 figure scripts, one per figure, plus the shared
                          _style.py, _networks.py, _ordering.py and
                          _positionality.py
code/examples/quickstart.py   descriptive tables and network summaries, stdlib only
data/raw/                 ALTO XML cache (git-ignored, ~76 MB, re-fetchable)
data/interim/             line stream and segmented entries (git-ignored)
data/processed/           the dataset + source_manifest.json (committed)
output/figures/           every figure as PNG and PDF
output/tables/            the population comparison tables
docs/                     codebook, provenance, figure index, validation report
tests/                    parsing-rule unit tests and dataset integrity checks
```

## Rebuilding from source

Python 3.11+, standard library only — no third-party dependencies. CI runs every
stage on a runner with nothing installed, so that is enforced rather than
promised. (The figures in `code/figures/` are the exception and have their own
`requirements.txt`; nothing there is needed to build or use the dataset.)

```sh
make all        # fetch, build, segment, extract, network, code, measure, compare, validate
make coding     # just the interpretive layer (community, positionality, gender)
make compare    # -> output/tables/comparison_tables.md
make measures   # -> data/processed/person_network_measures.csv
make test       # parsing-rule unit tests + dataset integrity checks
make data       # just the download (~20 min, polite to Gallica, resumable)
python3 code/pipeline/extract_records.py   # re-run one stage after editing
```

Each stage caches its output, so re-running after a change to one rule costs
seconds rather than a re-download. `data/raw/` and `data/interim/` are
git-ignored; `make all` regenerates everything in `data/processed/` bit for bit.

Rebuilding is reproducible in a strict sense. From the cached OCR, every
committed artefact — all seventeen CSVs, the source manifest, the validation
report and the comparison tables — comes back byte for byte, in about 50
seconds. The figures do too, in both PNG and PDF. Nothing that reaches an
output is ordered by a dictionary or a set, so a rebuild does not shuffle its
own results, and a diff under `data/processed/` or `output/` always signals a
real change rather than rebuild noise.

CI enforces the part it can reach. It has neither the 76 MB OCR cache nor the
plotting packages, so it regenerates the three stages that need only the
committed CSVs — the validation report, the comparison tables and
`person_network_measures.csv` — and fails if any differs from what is
committed. The core tables and the figures are checked the same way, but by
hand before a commit rather than by the runner.

## Using the network files

`network_nodes.csv` and `network_edges.csv` load directly into Gephi (import as
a node table and an edge table) or into igraph/NetworkX:

```python
import csv, networkx as nx

G = nx.Graph()
for n in csv.DictReader(open("data/processed/network_nodes.csv")):
    G.add_node(n["node_id"], **n)
for e in csv.DictReader(open("data/processed/network_edges.csv")):
    # startswith, not != "ambiguous": there are two ambiguous resolutions,
    # `ambiguous` and `ambiguous_fuzzy`, and both mean the same thing — the
    # surname matched more than one person, so the tie names nobody in
    # particular. Testing only the first would readmit 27 unresolved ties.
    if e["edge_type"] == "affiliation" and not e["resolution"].startswith("ambiguous"):
        G.add_edge(e["source"], e["target"], role=e["role"])
```

The affiliation network is two-mode (people × organisations). Prefer analysing
it as such; `edges_person_person.csv` offers a one-mode projection for
convenience, with large membership rolls excluded.

If all you need is each person's position rather than the graph itself,
`person_network_measures.csv` already carries degree, betweenness, closeness and
clustering for both networks, computed within each node's component and flagged
for whether that component is the giant one. Read the codebook entry first: the
measures are not comparable across components, and a blank there means the
person is absent from that network, which is not the same as a score of zero.

`code/examples/quickstart.py` reproduces a set of descriptive tables and network
summaries using only the standard library.

## Figures

`code/figures/` holds 63 descriptive, exploratory and comparative figures, one
script and one output file each, in PNG and PDF. They cover birth cohorts and
occupational composition; the two honours systems and how they overlap;
associational life; the affiliation network and its co-membership projection;
the bodies seen as an interlock and the places seen as a route map; career
sequences; the two communities compared, and the colonist/native line beside
them; who brokers between otherwise unconnected parts of the network, and how
few removals would break it; how much of the network's structure the projection
manufactures rather than finds; and whether the OCR is what limits the dataset.

Each figure's title states a claim rather than naming a chart type, and
[`docs/figures.md`](docs/figures.md) indexes all 63 by that claim — a test holds
the index to the titles the figures actually render. The design notes at the end
of that file record the palette checks.

```sh
pip install -r requirements.txt
make figures
```

Matplotlib, NetworkX and SciPy are needed for the figures only; the pipeline
itself stays standard-library-only.

## Provenance and verification

Every row carries `page_url`, which opens the exact page on Gallica. Coded
fields sit beside the verbatim `_raw` strings they were derived from, and each
tie carries an `evidence` snippet. Segmentation and classification decisions are
recorded per row (`segmentation_rule`, `classification_rule`) rather than
discarded, so the dataset can be audited and re-coded rather than taken on
trust.

`make test` runs 123 checks in seven files: the parsing rules are pinned to the
OCR strings that once broke them, the committed tables are checked for joins and
documented value domains, the counts are held against Lambert's own preface
figures, the derived measures are checked against the edge lists they come from,
the interpretive codings are checked against the rules that produced them, and
the figure index is checked against the titles the figures actually render. They
need no network access and no third-party packages.

Several of those checks exist because something went wrong. The parsing tests
carry the OCR strings that broke them; the figure-index test was added after a
title was reworded and the index quietly went on describing a figure that no
longer existed; the positionality tests pin two coding bugs that had reached
committed figures and, between them, reversed a finding. A test in this
repository is usually a scar, not a precaution.

## Licence and citation

Code and derived data: MIT (see `LICENSE`). The underlying volume is in the
public domain; the digitisation is by the Bibliothèque nationale de France,
whose [conditions of use](https://gallica.bnf.fr/edit/und/conditions-dutilisation-des-contenus-de-gallica)
apply to the source images.

Cite the source volume alongside the dataset:

> Lambert, Paul. 1912. *Dictionnaire illustré de la Tunisie: choses et gens de
> Tunisie*. Tunis: C. Saliba aîné. Digitised by the Bibliothèque nationale de
> France, ark:/12148/bpt6k5505300s.

See `CITATION.cff` for the dataset citation.
