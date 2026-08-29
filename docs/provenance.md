# Provenance and method

How the dataset was made, in enough detail to reproduce it, disagree with it, or
re-code it differently.

## 1. Source and acquisition

Paul Lambert, *Dictionnaire illustré de la Tunisie: choses et gens de Tunisie*
(Tunis: C. Saliba aîné, 1912), 4-XIV-468 pages, digitised by the Bibliothèque
nationale de France as [ark:/12148/bpt6k5505300s](https://gallica.bnf.fr/ark:/12148/bpt6k5505300s)
in 494 views. The work is in the public domain; BnF estimates its OCR at roughly
96% character accuracy.

Two Gallica services are used, both documented and openly reachable:

| endpoint | what it gives |
|---|---|
| `/iiif/ark:/12148/<ark>/manifest.json` | the view list and each view's printed-page label |
| `/RequestDigitalElement?O=<ark>&E=ALTO&Deb=<view>` | the per-view ALTO XML OCR, with coordinates and per-word confidence |

Nothing is taken from the HTML reading interface, which sits behind a
proof-of-work challenge; no challenge is circumvented anywhere in this pipeline.
Downloads run three at a time with exponential backoff, and are cached on disk,
so a re-run costs nothing and the volume is fetched once.

Views 25–492 are the dictionary proper (printed pages 1–468). Views 1–24 are
advertisements and the preface; 493–494 the endpapers. The mapping is exact:
**view = printed page + 24**.

## 2. From ALTO to a readable line stream

`code/pipeline/build_text.py`. Four problems had to be solved before the text was usable.

**Encoding.** The ALTO files declare `ISO-8859-1` but are UTF-8. Decoding by the
declaration turns every accented character into mojibake.

**Hyphenation.** Words broken across lines are stored twice in ALTO — the
fragment in `CONTENT`, the reconstructed word in `SUBS_CONTENT` on both halves.
Reading `CONTENT` alone leaves broken words; reading both halves duplicates every
hyphenated word. The reconstructed form is taken once, from the first fragment.

**Columns.** The page is set in two columns, but neither the page centre nor the
widest gap between line starts locates the gutter reliably: the scans are cropped
unevenly, and illustrated entries wrap their text around a portrait in a *narrow
inset* measure, adding a third and fourth left edge. The gutter is therefore
computed from full-measure blocks only, and each narrow inset is then assigned to
whichever column horizontally contains it. Within a column, blocks are read top
to bottom, with vertically overlapping blocks read left to right. Getting this
wrong interleaves two columns line by line and silently destroys every entry on
the page, so it is the single most consequential step in the pipeline.

**Running heads.** Each page carries a folio number and two alphabetical guide
words ("40 ATT — AUG"). Body text can sit as high as VPOS 287, so height alone
cannot identify them; a line is treated as a head only if it is among the topmost
lines of its page *and* matches the head shape. Left in, they inject
"24 MAC — MAÈ" into the middle of an entry.

The stage emits one record per OCR line with its coordinates, its mean word
confidence, and a **first-line indent** measured against a *local* baseline —
the median start position of the nine surrounding lines in the same measure. A
single column margin will not do, because page skew drifts the margin by 10–20
units down a column, which is the same order of magnitude as the indent itself.

## 3. Segmenting entries

`code/pipeline/segment_entries.py`. Lambert indents the first line of every paragraph, and
long association entries run to several paragraphs — so an indent marks a
paragraph, not necessarily an entry. Separating the two uses the one structural
property a dictionary guarantees, alphabetical order:

1. **Anchors.** Personal-name headwords are set in capitals, which makes them
   recognisable without typography (the ALTO carries no usable font style for
   this volume). Their sort keys must increase down the book, so a longest
   non-decreasing subsequence over the candidates yields a scaffold that is
   monotone by construction; garbled or spurious candidates drop out of it.
2. **Windows.** Any other indented paragraph becomes an entry only if its sort
   key falls between the last accepted headword and the next scaffold anchor.
   Organisation and place headwords sit inside that window; continuation
   paragraphs ("En 1900, elle a distribué...", "Tunis, rue d'Allemagne") do not,
   and are merged back into the entry above.
3. **Rubrics.** The volume's own in-entry labels — ETUDES, SUCCESS', TRAVAUX,
   BUT — are capitalised like surnames and are excluded by name, OCR variants
   included.
4. **Fallback shapes.** Where the indent is lost, two headword shapes still
   trigger a break: a capitalised surname followed by parenthesised forenames,
   and a place name followed by the administrative formula.

Comparisons use six-character truncated sort keys, which absorb OCR noise deep
inside long headwords, and four characters for the upper bound, which tolerates
the volume's own occasional mis-filings.

Portraits are located from ALTO `<Illustration>` elements and attached to the
entry whose text surrounds them. Of 532 illustrations in the dictionary proper,
436 have portrait proportions, against the preface's claim of 420 — and 422 fall
inside an entry.

## 4. Coding the entries

`code/pipeline/extract_records.py`. Lambert writes to three templates:

```
SURNAME (Forenames), <birth date>, <birthplace>, <honours>. <occupation>,
<address>. <date settled in Tunisia>. ETUDES : ... SUCCESS' : ... TRAVAUX : ...

PLACE. C. c. de <contrôle civil>, caïdat de <caïdat>, à <n> k. de <town>.
<description> POPUL. : <n> hab.

Association <name>. <foundation date>. Siège social : <address>. BUT : <aims>.
<n> membres. Prés., M. <name>; v.-prés., M. <name>; ...
```

Classification follows the templates, most specific rule first, and the rule
that fired is recorded on every row. The administrative formula ("C. c.",
"caïdat") is decisive for places, but only when it opens the description —
otherwise a person whose job is "Secrétaire de Contrôle civil" lands in the place
table.

Three coding decisions are worth flagging:

- **Honours are matched on fuzzy tokens**, with a bounded edit distance over a
  closed vocabulary, because the OCR renders "Nichan-Iftikhar" as
  "Nichan-lftikhar", "Nichan-Iflikliar", and worse. Literal matching loses
  roughly a fifth of them. Tolerances are set per word and tightened for short
  targets (an exact match is required for "olaf", because "olf." is the OCR's
  rendering of "off.").
- **Years are read with OCR digit repair** (S→8, O→0, l/I→1, C/G→6), then
  range-checked. Without it, "1S76" fails to parse and the *next* date in the
  entry — arrival in Tunisia — is silently taken as the birth year instead.
  The birth date is also required to sit within 45 characters of the forenames,
  where the template puts it.
- **Occupation is a multi-label field.** Keyword sets are applied to the
  occupation clause first and to the whole entry as a fallback;
  `occupation_primary` is the first match in a fixed priority order.

Nothing is imputed. A field that could not be read is empty.

## 5. Building ties

`code/pipeline/build_networks.py`. Three tie sources, of unequal quality, and the source is
recorded on every edge:

1. **Officer lists inside association entries** — explicit, role-bearing, current
   at publication. Both printed orders occur ("Prés., M. Marcille" and "Vilatte
   L.-E., prés."), and plural roles list several people at once.
2. **Memberships stated inside a person's own entry** — the person's own claim,
   and undated or retrospectively dated.
3. **Property lists inside place entries** — landowners named for a locality.

Names are matched to the volume's biographical entries by surname, with a
one-character tolerance flagged separately as `resolved_fuzzy`. Where two or more
people with entries share a surname, **no tie is assigned**: the mention is left
in `mentions.csv` marked `ambiguous`, for manual disambiguation. People named
only in someone else's entry become `person_named_only` nodes — they are real
members of this elite, just without a notice of their own.

Organisation-name variants are merged conservatively: only when one name's
distinctive tokens (four characters or more, excluding a stoplist) are a subset
of the other's and at least two are shared. That joins "Institut de Carthage" to
"Institut de Carthage, section scientifique" without collapsing every "Société"
into one node. A name with only one distinctive token is never merged, so some
variants of short names remain separate nodes.

The one-mode projection excludes bodies with more than 60 recorded members: a
membership roll of several hundred is not evidence that any two names on it knew
each other.

## 6. The interpretive layer: community and gender

Sections 2 to 5 describe transcription — turning what is printed into rows. This
section describes something different in kind: assigning people to categories
Lambert did not print. It is kept separate for that reason, produces its own
files rather than columns on `persons.csv`, and can be ignored entirely by
anyone who wants only what the volume states.

`code/pipeline/code_communities.py` codes each notice as European (French,
Italian, Maltese, other) or Tunisian (Muslim, Jewish). `code_gender.py` codes
gender. Both work from evidence tiers in the entry itself, in this order:
institutions held or attended, membership of a community body, birthplace, and
name particles or honorifics. Every classified row carries the evidence string
and a confidence, so a reader can disagree with a particular call rather than
with the file.

Two constraints are deliberate and worth stating plainly, because both cost
coverage:

- **No rule reads a surname.** Surname-based ethnic classification would raise
  coverage substantially and would encode the coder's assumptions rather than
  the volume's evidence. `tests/test_dataset.py` asserts that no rule does it.
- **Silence stays silence.** A Tunisia-born person with no other marker is
  flagged and left `unknown`, not assigned. 520 of 1,333 notices are uncoded for
  community and 185 for gender, and that is the honest number rather than a
  failure to try harder.

The results are 813 of 1,333 coded for community and 1,148 for gender, of whom
eleven are women. Eleven is small enough that most comparisons on gender are not
estimable, which `compare_populations.py` says rather than working around.

## 7. Derived measures and comparisons

`graph_metrics.py` implements connected components, Brandes betweenness,
Wasserman–Faust closeness and local clustering in the standard library. It exists
because this stage previously imported networkx, which broke the no-dependencies
promise the rest of the pipeline keeps: `make all` failed for anyone who followed
the README and installed nothing. On the graph in question the results match
networkx exactly for closeness, clustering and degree, and to 3.6e-16 for
betweenness.

`network_measures.py` writes those measures out per person. Each is computed
inside the node's own component, since centrality is undefined across
components, and the component size travels with it so that comparing a score
from a three-node component with one from the giant is at least a visible
mistake. Absence from a network is left blank rather than zero: a person with no
recorded tie has no betweenness, which is not a betweenness of nothing.

`compare_populations.py` writes the comparison tables. It uses Fisher exact
tests and permutation inference — both valid at these sample sizes — and states
explicitly where the models the source methodology specifies do not fit. One
detail matters for reproducibility: the sample fed to the permutation test is
sorted, because the test shuffles under a fixed seed and an unsorted list made
the resulting p-value depend on how the graph happened to be built rather than
on the data.

## 8. What is not solved

- **Merged entries.** Where the first-line indent is lost to OCR and no fallback
  shape matches, a notice is absorbed into the one above. This is the main reason
  the place and organisation counts fall a little short of Lambert's own.
- **Name variants.** People are matched by exact or one-character surname keys.
  Two spellings of the same person remain two nodes.
- **Undated ties.** Neither Lambert nor this pipeline dates most affiliations.
- **OCR floor.** Roughly 4% of characters are wrong, concentrated in proper
  names — which is precisely where the network's join key lives.

Each of these is measured, where it can be measured, in
[`validation_report.md`](validation_report.md).

## 9. Reproducibility

`code/pipeline/fetch_alto.py` downloads the ALTO and the IIIF manifest, caching
each view so the fetch is resumable and run once. `make all` rebuilds
`data/processed/` from that cache; `make data` refetches from Gallica. Python
3.11+, standard library only, no third-party dependencies, no network access
after the fetch stage. Each stage is independently runnable and caches its
output, so re-running one rule change costs seconds.

Rebuilding is reproducible in the strict sense. From the cached OCR every
committed artefact — all sixteen CSVs, the source manifest, the validation
report and the comparison tables — comes back byte for byte in about 50 seconds,
and the figures do too, in both PNG and PDF. That is a property worth protecting
rather than assuming, and it took three fixes to get: figure scripts that
iterated a set drew in hash order, one of them breaking a tie that named a
person in a caption, so a rebuild could change a stated fact; and Matplotlib
stamps a timestamp into every PDF unless told not to. Nothing that reaches an
output is now ordered by a dictionary or a set.

CI enforces the part it can reach. The runner has neither the OCR cache nor the
plotting packages, so it regenerates the three stages that need only the
committed CSVs — the validation report, the comparison tables and
`person_network_measures.csv` — and fails if any differs from what is committed.
`validate.py` recomputes the report from the committed files alone, which is why
it can run there at all.
