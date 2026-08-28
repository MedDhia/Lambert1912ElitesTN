# Figures

Descriptive, exploratory and comparative figures over the dataset in
`data/processed/`. One
script per figure, one output file per figure, written to `output/figures/` as
**PNG** (for reading) and **PDF** (vector, for inclusion in a paper).

```sh
pip install -r requirements.txt
make figures                       # render all of them
cd code/figures && python3 fig07_honour_systems.py   # or just one
```

The pipeline in `code/pipeline/` remains standard-library-only; nothing in
`requirements.txt` is needed to build or use the dataset itself.

## The figures

**Who they were**

| | Figure | What it shows |
|---|---|---|
| 1 | `fig01_birth_cohorts` | Birth decades: half the volume was born in the 1860s–70s |
| 2 | `fig02_occupations` | Occupational composition — a service elite |
| 3 | `fig03_age_at_settlement` | Age on arrival in Tunisia (median 27) |
| 4 | `fig04_settlement_timeline` | Arrivals by five-year period, against 1881 |
| 5 | `fig05_education` | Institutions named in the ETUDES rubric |
| 6 | `fig06_attention` | Entry length by whether the entry carries a portrait |

**Status and honours**

| | Figure | What it shows |
|---|---|---|
| 7 | `fig07_honour_systems` | French vs beylical recognition, mutually exclusive groups |
| 8 | `fig08_honour_grades` | Grade structure within each order |
| 9 | `fig09_honours_by_sector` | Dumbbell: which sectors each state decorates |
| 10 | `fig10_attention_and_honours` | Entry length by number of honours |

**Colonial geography and associational life**

| | Figure | What it shows |
|---|---|---|
| 11 | `fig11_localities_by_controle` | Localities per *contrôle civil* |
| 12 | `fig12_association_founding` | Cumulative foundings, 1860–1912 |
| 13 | `fig13_association_kinds` | What kind of bodies they were |

**Networks**

| | Figure | What it shows |
|---|---|---|
| 14 | `fig14_affiliation_network` | Two-mode people × bodies, largest component |
| 15 | `fig15_comembership_backbone` | One-mode co-membership core |
| 16 | `fig16_degree_distribution` | Rank–size of affiliation degree, log-log |
| 17 | `fig17_top_bodies_roles` | Role composition of the best-recorded bodies |
| 18 | `fig18_career_transitions` | Sector-to-sector moves in career sequences |

**Populations compared**

| | Figure | What it shows |
|---|---|---|
| 19 | `fig19_community_composition` | European and Tunisian communities in the volume |
| 20 | `fig20_honours_by_community` | Honours and portraits across the two communities |
| 21 | `fig21_women_in_the_record` | Every notice as one mark; the eleven women |
| 22 | `fig22_occupations_by_community` | Near-identical occupational profiles |
| 23 | `fig23_education_by_community` | Where each community was schooled |
| 24 | `fig24_community_mixing` | Co-membership across communities, against chance |
| 25 | `fig25_network_by_community` | The affiliation network, coloured by community |

**Honours, and the record itself**

| | Figure | What it shows |
|---|---|---|
| 26 | `fig26_honour_cooccurrence` | Which orders were held together |
| 27 | `fig27_awarding_states` | Sixteen awarding authorities; two that matter |
| 28 | `fig28_landowners_and_localities` | Named landowners, and how few have a notice |
| 29 | `fig29_ocr_and_recovery` | Field recovery against OCR confidence |

**Brokerage**

Figures 14, 15 and 25 size nodes by degree, which finds the big bodies. These
four size by betweenness, which finds the people the network would fall apart
without. They share `_networks.py`, which also documents why a handful of
generically-named organisation nodes are excluded from them.

| | Figure | What it shows |
|---|---|---|
| 30 | `fig30_broker_affiliation_network` | Two-mode network, area linear in betweenness |
| 31 | `fig31_broker_comembership_by_community` | The same for co-membership, coloured by community |
| 32 | `fig32_degree_vs_betweenness` | What betweenness adds to degree, and what it does not |
| 33 | `fig33_broker_ego_networks` | The bodies four brokers alone hold together |

## Design notes

Colours come from a validated reference palette, and the subsets used here were
re-checked with the palette validator rather than eyeballed:

| Use | Check | Result |
|---|---|---|
| Two-series (grouped bars, dumbbell) | all-pairs | PASS |
| Network node classes | all-pairs (scatter forms cap at 3) | PASS |
| Four-part stacked bar | adjacent pairs | PASS, contrast WARN on aqua/yellow |
| Ordered categories | ordinal ramp | PASS |
| Sequential magnitude (fig. 26 matrix) | single hue, light to dark | PASS |

Node **area** is linear in betweenness wherever it encodes it, so a mark twice
the area brokers twice the paths. The scale is deliberately not square-rooted:
two thirds of the nodes sit on no shortest path at all, and a compressing
transform would flatter those zeroes into looking like small positive values.
A floor size keeps them visible as points without pretending they broker
anything. Because marks then vary hugely in size, `annotate_nodes` takes each
label's clearance from its own mark's radius — at a fixed offset a label's
backing patch covers the very node it names.

Three of the four categorical slots are the ceiling for a scatter or network
form, which is why fig. 25 draws the associations as hollow rings rather than
taking a fourth hue: the three person classes are the only fills in the plot.
Where a null model is shown beside an observation (fig. 24), the null takes the
de-emphasis grey rather than a hue — it is a benchmark, not a series.

Where the validator returns a contrast warning, those segments carry direct
labels — the "relief" the warning obliges. Sequential magnitude uses one hue,
light to dark; categorical colour is used only where the series *are* the
subject; and where one number is the story, the rest of the bars recede to a
lighter step rather than taking a hue of their own.

Two further conventions:

- **The title states the claim; the subtitle carries the n and the caveat.** If
  a figure's title asserts something the chart does not support, that is a bug.
- **No value is reachable only by looking at a colour.** Every figure is drawn
  from a CSV in `data/processed/`, which is the table view; bar charts label
  their tips directly rather than making the reader measure against a grid.

Figures inherit every limitation of the dataset — see `docs/validation_report.md`.
Two matter most when reading them: coverage is Lambert's coverage, not a
population, and an absent value (no honour named, no occupation coded) means the
volume did not print it, not that the thing was not so.
