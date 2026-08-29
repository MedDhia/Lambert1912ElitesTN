# Figures

Sixty-three descriptive, exploratory and comparative figures over the dataset in
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
| 49 | `fig49_centrality_and_honours` | The most decorated sit on nine times as many paths as the undecorated |

**Colonial geography and associational life**

| | Figure | The claim |
|---|---|---|
| 11 | `fig11_localities_by_controle` | Coverage follows the colonial administration, and thickens around Tunis |
| 12 | `fig12_association_founding` | Associational life is a creation of the Protectorate's second generation |
| 13 | `fig13_association_kinds` | Chambers, mutual aid and professional bodies dominate the associational field |
| 28 | `fig28_landowners_and_localities` | The named owners of the land are mostly not the people in the book |
| 39 | `fig39_locality_infrastructure` | For half the localities the volume records no amenity at all |
| 40 | `fig40_association_size` | A membership roll and a committee are not the same kind of tie |
| 51 | `fig51_place_network` | Every route runs through Tunis |

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
| 44 | `fig44_interlock_network` | The associations interlock through one shared member at a time |
| 48 | `fig48_office_and_position` | Holding office is a structural position, not just a title |

**How much of the structure is the projection's own**

The one-mode network is built by turning every body into a clique of its
members, and that operation manufactures structure: triangles, hubs of equal
degree, dense cores. These five ask how much of what the network figures show
survives that objection, and answer plainly where it does not.

| | Figure | The claim |
|---|---|---|
| 45 | `fig45_k_core` | Forty-one people each share a body with forty of the others |
| 46 | `fig46_small_world` | Any two of these people are four handshakes apart |
| 47 | `fig47_degree_assortativity` | The projection says hubs cluster together; the raw graph says the opposite |
| 50 | `fig50_structural_holes` | Constraint here measures how few people you know, not how closed they are |
| 52 | `fig52_two_mode_marginals` | Both sides of the network are mostly ones |

**The two communities compared**

| | Figure | The claim |
|---|---|---|
| 19 | `fig19_community_composition` | Five Europeans recorded for every Tunisian |
| 20 | `fig20_honours_by_community` | Where recognition divides, it favours the Tunisians |
| 21 | `fig21_women_in_the_record` | Eleven women in a volume of 1,307 notables |
| 22 | `fig22_occupations_by_community` | The two communities are recorded in much the same trades |
| 23 | `fig23_education_by_community` | The Islamic institutions educate Tunisians only — the French ones educate both |
| 24 | `fig24_community_mixing` | Europeans and Tunisians belonged to the same bodies less often than chance |
| 25 | `fig25_network_by_community` | Tunisian notables sit inside the network, not on its rim |

**Positionality: colonist and native**

The figures above ask which of the volume's *communities* a person belonged to.
These ask a different question of the same evidence: on which side of the
colonial relation the record places them — colonist (European-origin, settler or
metropolitan) or native (Tunisian-origin, Muslim and Jewish alike, which is the
volume's own usage). `code/pipeline/code_positionality.py` documents the mapping,
the one rule it adds, and that rule's measured error rate.

Read figs. 54 and 55 before the rest. A third of the volume cannot be placed at
all, and the two sides are reached by different kinds of evidence — natives
mostly through a communal institution, colonists mostly through a European
birthplace. Since institutional ties are also what put a person in the network,
the raw comparison measures the coding rather than the elite. Figs. 56 to 63 are
drawn on a matched basis for that reason, and `_positionality.py` holds the
restriction in one place.

| | Figure | The claim |
|---|---|---|
| 54 | `fig54_positionality_coding` | A third of this elite cannot be placed on either side of the colonial line |
| 55 | `fig55_identification_artefact` | How a person was identified moves this measure more than which side he was on |
| 56 | `fig56_position_in_network` | Natives broker as much as colonists, from fewer memberships and further out |
| 57 | `fig57_position_and_honours` | Both states decorated both sides at the same rate |
| 58 | `fig58_position_and_attention` | The volume gives both sides the same space on the page |
| 59 | `fig59_position_and_occupation` | The native administration is a career ladder with almost no colonists on it |
| 60 | `fig60_position_and_cohort` | Only one side of this elite has a date of arrival |
| 61 | `fig61_positionality_network` | Natives sit inside the network, in clumps rather than on the rim |
| 62 | `fig62_position_mixing` | Colonists and natives belonged to the same bodies far less often than chance |
| 63 | `fig63_native_muslim_and_jewish` | The native side is two populations: one in the state, one in the professions |

Taken together they say something narrower than "the colonial line organised
this elite" and something more specific. Among the people Lambert chose to
print, the line is nearly invisible in what the two states awarded (57), in the
space the volume gave them (58), and in how much of the network's brokerage they
carried (56). It is unmistakable in two places: which part of the state they
served (59), and who they sat on committees with (62). The last of those is the
strongest single result in this repository.

**Brokerage**

Figures 14, 15 and 25 size nodes by degree, which finds the big bodies. These
five rank by betweenness, which finds the people the network would come apart
without — a different question, and a different answer. They share
`_networks.py` for graph construction and `_ordering.py` for ranking.

| | Figure | The claim |
|---|---|---|
| 30 | `fig30_broker_affiliation_network` | Brokerage is far more concentrated than membership |
| 31 | `fig31_broker_comembership_by_community` | The brokers are not all Europeans |
| 32 | `fig32_degree_vs_betweenness` | Degree mostly predicts brokerage — and misses the people who matter most |
| 33 | `fig33_broker_ego_networks` | Take one person out and these bodies stop touching |
| 53 | `fig53_attack_tolerance` | Eighty people hold four fifths of this network together |

Every figure that builds its graph through `_networks.py` — these five and the
structural figures above — excludes sixteen organisation nodes whose printed
name is a bare common noun ("Société", "Municipalité") and which therefore merge
bodies the volume never distinguishes: 48 of the 1,639 ties those figures read,
under 3%. The exclusion matters most here, because betweenness does not merely
blur across such a merge; it invents a path and then rewards whatever sits on
it. `_networks.py` documents the rule and its limits.

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
