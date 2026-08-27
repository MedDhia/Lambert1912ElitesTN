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
| Honours coded (person × order) | 1,810 |
| Career posts | 1,449 |
| Educational institutions attended | 1,158 |
| Affiliation ties (person → organisation) | 1,761 |
| Person → place ties (birth, residence, property) | 2,104 |
| Network nodes / edges | 4,008 / 3,865 |

Lambert's preface states his own totals — "more than 1,300" biographies, "more
than 750" localities, "more than 175" societies, 420 portraits. The pipeline
never sees those figures, so they serve as an independent check: it recovers
100%, 98%, 91% and 100% of them respectively. See
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
- **The volume as an object of study.** Entry length, portrait presence, and the
  editorial rubrics are measures of the compiler's own hierarchy of attention.

## What it is not

It is not a census, a sample, or a population register. Inclusion was decided in
1912 by a Tunis publisher, and the selection is heavily French, urban, male, and
propertied. Tunisian Muslims and Jews appear mainly as notables, officials, and
merchants; women are almost absent. Ties are undated and cross-sectional. Read
the limitations section of the validation report before treating any count as a
population quantity — the dataset is evidence about a colonial elite's
self-representation, and is most defensible when used as such.

## Layout

```
src/                      the pipeline, five stages, each runnable on its own
  fetch_alto.py           download the BnF ALTO OCR and IIIF manifest (cached)
  build_text.py           ALTO -> column-aware, de-hyphenated line stream
  segment_entries.py      line stream -> dictionary entries
  extract_records.py      entries -> typed records and variables
  build_networks.py       records -> mentions, ties, nodes and edges
  validate.py             -> docs/validation_report.md
data/raw/                 ALTO XML cache (git-ignored, ~76 MB, re-fetchable)
data/interim/             line stream and segmented entries (git-ignored)
data/processed/           the dataset + source_manifest.json (committed)
docs/                     codebook, provenance, validation report
examples/quickstart.py    descriptive tables and network summaries, stdlib only
figures/                  18 descriptive and network figures, one script each
tests/                    parsing-rule unit tests and dataset integrity checks
```

## Rebuilding from source

Python 3.11+, standard library only — no third-party dependencies.

```sh
make all        # fetch, build, segment, extract, network, validate
make test       # parsing-rule unit tests + dataset integrity checks
make data       # just the download (~20 min, polite to Gallica, resumable)
python3 src/extract_records.py   # re-run one stage after editing its rules
```

Each stage caches its output, so re-running after a change to one rule costs
seconds rather than a re-download. `data/raw/` and `data/interim/` are
git-ignored; `make all` regenerates everything in `data/processed/` bit for bit.

## Using the network files

`network_nodes.csv` and `network_edges.csv` load directly into Gephi (import as
a node table and an edge table) or into igraph/NetworkX:

```python
import csv, networkx as nx

G = nx.Graph()
for n in csv.DictReader(open("data/processed/network_nodes.csv")):
    G.add_node(n["node_id"], **n)
for e in csv.DictReader(open("data/processed/network_edges.csv")):
    if e["edge_type"] == "affiliation" and e["resolution"] != "ambiguous":
        G.add_edge(e["source"], e["target"], role=e["role"])
```

The affiliation network is two-mode (people × organisations). Prefer analysing
it as such; `edges_person_person.csv` offers a one-mode projection for
convenience, with large membership rolls excluded.

`examples/quickstart.py` reproduces a set of descriptive tables and network
summaries using only the standard library.

## Figures

`figures/` holds 18 descriptive and exploratory figures — birth cohorts,
occupational composition, the two honours systems, associational life, the
affiliation network and its co-membership projection, career transitions — one
script and one output file each, in PNG and PDF. See
[`figures/README.md`](figures/README.md) for the index and the design notes.

```sh
pip install -r figures/requirements.txt
make figures
```

Matplotlib and NetworkX are needed for the figures only; the pipeline itself
stays standard-library-only.

## Provenance and verification

Every row carries `page_url`, which opens the exact page on Gallica. Coded
fields sit beside the verbatim `_raw` strings they were derived from, and each
tie carries an `evidence` snippet. Segmentation and classification decisions are
recorded per row (`segmentation_rule`, `classification_rule`) rather than
discarded, so the dataset can be audited and re-coded rather than taken on
trust.

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
