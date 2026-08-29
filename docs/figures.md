# Figures

Forty-three descriptive, exploratory and comparative figures over the dataset in
`data/processed/`. One script per figure, each writing two files to
`output/figures/`: a **PNG** to read and a **PDF** to place in a paper.

```sh
pip install -r requirements.txt
make figures                       # render all of them
cd code/figures && python3 fig07_honour_systems.py   # or just one
```

The pipeline in `code/pipeline/` remains standard-library-only; nothing in
`requirements.txt` is needed to build or use the dataset itself.

## The figures

Each row below is the figure's own claim, not a description of its chart type —
the same title it carries when rendered. Figures are grouped by subject; the
numbers are filenames and run in the order the figures were written.

**Who they were**

| | Figure | The claim |
|---|---|---|
| 1 | `fig01_birth_cohorts` | Half the volume was born in the 1860s and 1870s |
| 2 | `fig02_occupations` | A service elite: soldiers, officials, lawyers and doctors first |
| 3 | `fig03_age_at_settlement` | They arrived young — a career made in the Protectorate, not brought to it |
| 4 | `fig04_settlement_timeline` | Arrivals track the Protectorate, not the conquest |
| 5 | `fig05_education` | A French secondary education is the common credential |
| 6 | `fig06_attention` | A portrait comes with roughly twice the words |
| 34 | `fig34_honours_by_cohort` | Honours accumulate with time served |
| 35 | `fig35_origins_and_residence` | A scattered origin, a single destination |
| 36 | `fig36_credentials` | A secondary certificate, not a doctorate, is what this elite carries |

**Status and honours**

| | Figure | The claim |
|---|---|---|
| 7 | `fig07_honour_systems` | The Bey's order reaches four times as many people as the Légion d'honneur |
| 8 | `fig08_honour_grades` | The beylical order is granted freely at the middle grades |
| 9 | `fig09_honours_by_sector` | Both states decorate office-holders and soldiers; only the Bey decorates traders |
| 10 | `fig10_attention_and_honours` | More honours, more column inches — the volume ranks as the state ranks |
| 26 | `fig26_honour_cooccurrence` | The Bey's order accompanies the French ones; it does not replace them |
| 27 | `fig27_awarding_states` | Two states did the decorating; sixteen awarding authorities appear in all |

**Colonial geography and associational life**

| | Figure | The claim |
|---|---|---|
| 11 | `fig11_localities_by_controle` | Coverage follows the colonial administration, and thickens around Tunis |
| 12 | `fig12_association_founding` | Associational life is a creation of the Protectorate's second generation |
| 13 | `fig13_association_kinds` | Chambers, mutual aid and professional bodies dominate the associational field |
| 28 | `fig28_landowners_and_localities` | The named owners of the land are mostly not the people in the book |
| 39 | `fig39_locality_infrastructure` | For half the localities the volume records no amenity at all |
| 40 | `fig40_association_size` | A membership roll and a committee are not the same kind of tie |

**Networks**

| | Figure | The claim |
|---|---|---|
| 14 | `fig14_affiliation_network` | One connected elite: two thirds of all affiliation ties form a single component |
| 15 | `fig15_comembership_backbone` | Four in five committee-sharers sit in a single connected core |
| 16 | `fig16_degree_distribution` | A few bodies carry the network; almost everyone belongs to one thing |
| 17 | `fig17_top_bodies_roles` | Mostly office-holders — except where the volume prints a membership roll |
| 18 | `fig18_career_transitions` | Careers move between the army, the administration and the courts |
| 37 | `fig37_career_length` | Three quarters of the notices print no career sequence at all |
| 38 | `fig38_career_sector_change` | Most careers cross a sector line; half still end where they began |
| 42 | `fig42_network_components` | Four in five people sit in one component; the rest sit in fragments |

**The two communities compared**

| | Figure | The claim |
|---|---|---|
| 19 | `fig19_community_composition` | Four Europeans recorded for every Tunisian |
| 20 | `fig20_honours_by_community` | Recognition does not divide along the colonial line |
| 21 | `fig21_women_in_the_record` | Eleven women in a volume of 1,307 notables |
| 22 | `fig22_occupations_by_community` | The two communities are recorded in much the same trades |
| 23 | `fig23_education_by_community` | The Islamic institutions educate Tunisians only — the French ones educate both |
| 24 | `fig24_community_mixing` | Europeans and Tunisians belonged to the same bodies less often than chance |
| 25 | `fig25_network_by_community` | Tunisian notables sit inside the network, not on its rim |

**Brokerage**

Figures 14, 15 and 25 size nodes by degree, which finds the big bodies. These
four size by betweenness, which finds the people the network would come apart
without — a different question, and a different answer. They share
`_networks.py` for graph construction and `_ordering.py` for ranking.

| | Figure | The claim |
|---|---|---|
| 30 | `fig30_broker_affiliation_network` | Brokerage is far more concentrated than membership |
| 31 | `fig31_broker_comembership_by_community` | The brokers are not all Europeans |
| 32 | `fig32_degree_vs_betweenness` | Degree mostly predicts brokerage — and misses the people who matter most |
| 33 | `fig33_broker_ego_networks` | Take one person out and these bodies stop touching |

These four exclude sixteen organisation nodes whose printed name is a bare
common noun ("Société", "Municipalité") and which therefore merge bodies the
volume never distinguishes — 48 of the 1,639 ties these figures read, under 3%.
Betweenness does not merely blur across such a merge; it invents a path and then
rewards whatever sits on it.
`_networks.py` documents the rule and its limits.

That filter is why the figures' numbers differ slightly from
`data/processed/person_network_measures.csv`, which exports the same measures
for every person from the *unfiltered* edge lists, so that the dataset stays a
function of its published inputs rather than of a figure's editorial choice. Use
the exported columns for modelling; read these figures for the shape.

**The record as an object of study**

| | Figure | The claim |
|---|---|---|
| 29 | `fig29_ocr_and_recovery` | OCR quality is not what limits the dataset |
| 41 | `fig41_name_resolution` | Most names the volume drops are people it never gave an entry |
| 43 | `fig43_who_writes` | Medicine publishes four times as often as the administration |

Figures 6 and 10 belong here too, and are listed above only because entry length
is easier to read beside the attributes it tracks.

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

### Reproducibility

Rendered output is committed, so a figure that draws differently on each run
produces a spurious diff every time the figures are rebuilt — and if the varying
thing feeds a caption, the figure states a different fact each time. Both
happened here before the rule below existed: `fig28` drew its edges in a set's
iteration order, and `fig32` picked "the broker holding fewest ties" with `min`
over a set, naming Nestler on some runs and Vendel on others.

**Never let a set's iteration order reach the output.** Sort it. Where nodes are
ranked by a score, go through `ranked`, which sorts on `(-score, node id)` so
ties break on something stable rather than on the interpreter's hash seed.
`tests/test_figure_determinism.py` enforces this: it unit-tests the ordering
rule and fails the build if a figure ranks betweenness inline.

The rule lives in `_ordering.py` and is re-exported by `_networks.py`, so the
figures reach it as `N.ranked`. The split is deliberate and tested: `_ordering`
imports nothing outside the standard library, which is what lets the test suite
load it on CI, where the plotting dependencies are not installed.

The same concern applies to the files themselves. Matplotlib's PDF backend
stamps the current time into `/CreationDate`, so an otherwise identical rebuild
rewrote all 33 PDFs and every commit carried a binary diff that meant nothing;
`_style.save` passes `metadata={"CreationDate": None}` to suppress it. Both
formats now reproduce byte for byte on a given machine, so a diff in
`output/figures/` means the figure actually changed. The one piece of varying
metadata left is `/Producer`, which records the Matplotlib version — that
*should* change when the library does.

Figures inherit every limitation of the dataset — see `docs/validation_report.md`.
Two matter most when reading them: coverage is Lambert's coverage, not a
population, and an absent value (no honour named, no occupation coded) means the
volume did not print it, not that the thing was not so.
