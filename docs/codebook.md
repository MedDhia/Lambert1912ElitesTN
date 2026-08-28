# Codebook

Every table is a CSV in `data/processed/`, UTF-8, comma-separated, with a header
row. **An empty cell means the value could not be read from the page** — either
Lambert did not print it, or the OCR lost it. Nothing is imputed anywhere in the
pipeline, and no cell is filled by inference from another record.

Two conventions run through all the tables:

- Fields ending in `_raw` hold the verbatim string as the OCR read it, including
  its errors. Coded fields sit alongside them. Keeping both means any coded
  value can be checked against the source without re-running the pipeline.
- Every row carries the printed page and a `page_url` pointing at that page's
  image on Gallica, so any cell can be verified against the original in one
  click.

Unit of observation, by table:

| file | one row is | n |
|---|---|---|
| `entries.csv` | a dictionary entry | 2,741 |
| `persons.csv` | a person with a biographical notice | 1,307 |
| `places.csv` | a locality with a notice | 736 |
| `organizations.csv` | an association or public body with a notice | 159 |
| `decorations.csv` | a person × an honour | 1,810 |
| `career_positions.csv` | a person × a post in their career sequence | 1,449 |
| `education.csv` | a person × an educational institution | 1,158 |
| `mentions.csv` | a person named inside someone else's entry | 1,099 |
| `edges_person_organisation.csv` | an affiliation tie | 1,761 |
| `edges_person_place.csv` | a person-to-place tie | 2,104 |
| `edges_person_person.csv` | a co-membership tie | 5,378 |
| `network_nodes.csv` | a node in the combined network | 4,008 |
| `network_edges.csv` | an edge in the combined network | 3,865 |
| `person_communities.csv` | a person × their coded community | 1,307 |
| `person_gender.csv` | a person × their coded gender | 1,307 |

`data/processed/source_manifest.json` sits alongside them: the ark, the number
of IIIF views, and how many carry an ALTO OCR layer. It is written by the fetch
stage and committed, so the validation report reads the same in a fresh clone as
it does on the machine that ran the download.

---

## entries.csv

The base corpus: every entry the segmenter found, whatever its type. Use this to
re-code anything differently — the full text of each entry is here.

| variable | type | definition |
|---|---|---|
| `entry_id` | string | Stable key, `L1912-#####`, assigned in reading order. Used as the join key everywhere and as the node id in the network files. |
| `headword` | string | The headword as printed, OCR errors included. |
| `sort_key` | string | Headword normalised for alphabetical comparison (accents and punctuation stripped, upper-cased). |
| `entry_type` | categorical | `person`, `place`, `organisation`, `topic`, `cross_reference`. See the classification rules below. |
| `classification_rule` | categorical | Which rule assigned `entry_type`. Lets you filter to the high-confidence rules (`administrative_unit`, `forenames_and_life_dates`, `organisational_template`) or audit the residual ones. |
| `segmentation_rule` | categorical | `anchor_surname` (a capitalised personal headword in the monotone alphabetical scaffold) or `alphabetical_window` (accepted because its sort key fell between the surrounding anchors). |
| `page_first`, `page_last` | string | Printed page numbers the entry spans. Roman numerals for front matter. |
| `view_first`, `view_last` | integer | Gallica IIIF view numbers (= printed page + 24 in the dictionary proper). |
| `n_chars` | integer | Length of the entry text. A serviceable measure of how much attention Lambert gave the subject. |
| `n_paragraphs` | integer | Paragraphs merged into this entry. Values above ~4 flag entries where segmentation may have absorbed a following notice. |
| `n_portraits` | integer | Portrait photogravures printed inside the entry. |
| `ocr_confidence` | float 0–1 | Mean per-word confidence reported by the BnF OCR for this entry's words. Volume mean 0.926. |
| `page_url` | string | Gallica page viewer for `view_first`. |
| `image_url` | string | IIIF full-resolution image of that page. |
| `text` | string | The entry text, columns re-ordered, hyphenation resolved, running heads removed. |

### Classification rules

| rule | meaning | assigned type |
|---|---|---|
| `administrative_unit` | The entry opens with the administrative formula ("C. c. de Sousse, caïdat de Mahdia"). Unambiguous. | place |
| `forenames_and_life_dates` | Capitalised headword, parenthesised forenames, and a date in the opening. | person |
| `caps_headword_with_forenames` | Forenames but no date. | person |
| `caps_headword_with_date` / `_with_honour` / `_with_occupation` | Capitalised headword whose forenames were lost to OCR, identified by a life date, an honour, or a stated occupation. | person |
| `organisational_template` | Headword begins with an organisational noun, or the entry carries "BUT :", "Siège social", or an officer list. | organisation |
| `administrative_markers` / `_late` / `settlement_noun_and_measure` | Population, distance, or settlement nouns without the opening formula. | place |
| `see_also_only` | A short cross-reference ("Juifs. (V. Israélites.)"). | cross_reference |
| `residual` | None of the above: Arabic and Tunisian terms, flora and fauna, institutions, customs, statistics. | topic |

---

## persons.csv

| variable | type | definition |
|---|---|---|
| `entry_id` | string | Join key to `entries.csv`. |
| `surname` | string | Headword, i.e. the surname as filed. |
| `forenames` | string | Parenthesised forenames. Empty where Lambert prints none or the OCR lost the parenthesis. |
| `name_has_nasab_particle` | 0/1 | The printed name contains an Arabic patronymic particle as a **separate token** (BEN, BENT, OULD, ABD, ABOU, BOU, BEL, EL, SIDI, SI). **This is a feature of the printed name form, not an ethnic, national, or religious classification, and must not be used as one.** It is deliberately narrow: it does not fire on names written solid (ABDELLI, BOUHAGEB), so it under-counts Arabic-form names by a wide margin (18 rows). It is provided for text-level work on naming practice; for anything about community membership, read the entries. |
| `name_honorific` | string | `Si`, `Sidi`, `Hadj`, `Cheikh`, `Bey`, `Pacha` where present in the name. |
| `birth_date_raw` | string | Verbatim birth date. |
| `birth_year` | integer | Four-digit year, with OCR digit confusions repaired (S→8, O→0, l→1, C/G→6). Range-checked to 1600–1915; anything else is left empty, as is any date containing a stray `(`, which marks a character the OCR dropped and cannot be repaired without guessing. Coverage 87%. |
| `birth_place` | string | Place of birth, verbatim. |
| `birth_place_detail` | string | The parenthesised qualifier after it — usually a French *département* ("Gironde") or a country ("Algérie", "Sicile"). |
| `occupation_raw` | string | The occupation clause, from the end of the identification block (headword, forenames, birth, honours) to the address or the settlement date. |
| `occupation_categories` | string | Semicolon-separated categories matched anywhere in the occupation clause, falling back to the whole entry. **Multi-label**: a person can be `medicine_health;politics_native_admin`. |
| `occupation_primary` | categorical | The first matched category, in the fixed priority order listed below. Empty for 19% of persons, mostly where the OCR broke the occupation word. |
| `address_raw` | string | Street address as printed. |
| `city` | categorical | City in the address, matched against a closed list of Tunisian towns. |
| `settled_tunisia_raw` | string | The bare date Lambert prints after the occupation and address. |
| `settled_tunisia_year` | integer | Its year. **Interpreted, not labelled in the source**: throughout the volume this date is the year the person arrived in or settled in Tunisia, but Lambert never says so in the preface. Treat it as a coding decision that can be checked against `settled_tunisia_raw` and the page image. |
| `n_decorations` | integer | Distinct honours named in the entry. |
| `decoration_orders` | string | Semicolon-separated order keys; see `decorations.csv`. |
| `has_legion_honneur` | 0/1 | Légion d'honneur, any grade (n = 178). |
| `has_nichan_iftikhar` | 0/1 | Nichan Iftikhar, the beylical order, any grade (n = 707). |
| `education_raw` | string | Text of the ETUDES rubric. |
| `education_institutions` | string | Semicolon-separated institutions found in it. |
| `degrees` | string | Semicolon-separated qualifications: `licence_droit`, `doctorat_droit`, `doctorat_medecine`, `baccalaureat`, `brevet_superieur`, `agregation`, `diplome_superieur`, `certificat`. |
| `career_raw` | string | Text of the SUCCESS' (successivement) rubric: the career sequence. |
| `n_career_positions` | integer | Segments in that rubric — a rough count of posts held. |
| `works_raw` | string | Text of the TRAVAUX / OEUVRES / PUBLICATIONS rubric. |
| `has_works` | 0/1 | Whether that rubric is present: publications, buildings, missions. |
| `deceased_mentioned` | 0/1 | The entry records a death. Lambert covers "vivantes ou décédées" — living and dead. |
| `n_portraits` | integer | Portraits in the entry. |
| `n_chars` | integer | Entry length. |
| `page_first` | string | Printed page. |
| `ocr_confidence` | float | Mean OCR word confidence for the entry. |

### Occupation categories

Priority order, which is also the order `occupation_primary` resolves ties in:
`justice_law`, `medicine_health`, `military`, `education_science`, `religion`,
`engineering_architecture`, `administration`, `politics_native_admin`,
`diplomacy`, `commerce`, `industry_crafts`, `agriculture`, `finance_banking`,
`press_letters_arts`, `mining`, `transport_maritime`, `hospitality_services`.

`politics_native_admin` covers both elective office under the Protectorate
(deputy, municipal councillor, the Conférence consultative) and the beylical
administration (caïd, khalifa, governor). Anyone wanting to separate them should
recode from `occupation_raw`.

---

## places.csv

| variable | type | definition |
|---|---|---|
| `entry_id`, `place_name` | string | Key and headword. |
| `controle_civil` | string | The *contrôle civil* — the French civil administrative district. |
| `caidat` | string | The *caïdat* — the Tunisian administrative district under a caïd. Together these two columns give the dual administrative geography of the Protectorate. |
| `annexe` | string | The military or civil annexe, where named. |
| `distance_km`, `distance_from` | integer, string | "à 14 k. de Mahdia" → 14, Mahdia. |
| `population` | integer | Inhabitants, thousands separators removed. Coverage 18% — Lambert prints a figure for a minority of localities. |
| `altitude_m` | integer | Altitude in metres. |
| `tribe_mentioned` | string | Tribe named as the settlement's population. |
| `owners_raw` | string | The property-owner list ("Propr.: MM. Robert, Julien, Vernay"). Parsed into ties in `edges_person_place.csv`. |
| `has_railway_station` | 0/1 | A railway line, station, or halt is mentioned. |
| `has_school`, `has_post_office`, `has_market` | 0/1 | Colonial infrastructure mentioned in the entry. |
| `has_roman_ruins` | 0/1 | Ruins, Roman or Byzantine remains, or antiquities mentioned. |
| `archaeology_raw` | string | Text of the ARCH. rubric, contributed by Dr Carton (preface, p. III). |
| `n_chars`, `page_first`, `ocr_confidence` | | As above. |

These indicators record **what the entry mentions**, not what existed. A place
with `has_school = 0` may well have had a school Lambert did not name.

---

## organizations.csv

| variable | type | definition |
|---|---|---|
| `entry_id`, `organisation_name` | string | Key and headword. |
| `founded_raw`, `founded_year` | string, integer | Foundation date as printed and its year. |
| `seat_raw` | string | The "Siège social" line. |
| `city` | categorical | City of the seat. |
| `n_members_stated` | integer | Membership figure the entry states. |
| `purpose_raw` | string | The BUT (aims) rubric — the association's own statement of purpose, up to 600 characters. |
| `activities_raw` | string | The TRAVAUX rubric. |
| `organisation_kinds` | string | Semicolon-separated, multi-label. |
| `organisation_kind_primary` | categorical | First match: `mutual_aid`, `professional_union`, `chamber_public_body`, `learned_society`, `sport_leisure`, `alumni`, `masonic`, `religious`, `music_arts`, `national_community`, `agricultural_economic`. |
| `n_chars`, `page_first`, `ocr_confidence` | | As above. |

---

## decorations.csv

One row per person × honour.

| variable | type | definition |
|---|---|---|
| `entry_id`, `person` | string | Key and surname. |
| `order` | categorical | `legion_honneur`, `nichan_iftikhar`, `nichan_el_abed`, `nichan_ed_dem`, `palmes_academiques`, `merite_agricole`, `ouissam_alaouite`, `couronne_italie`, `medjidie`, `osmanie`, `etoile_noire_benin`, `etoile_anjouan`, `ordre_radama`, `saint_olaf`, `saint_stanislas`, `saint_sauveur_grece`, `isabelle_catholique`, `charles_iii`, `christ_portugal`, `francois_joseph`, `leopold_belgique`, `dannebrog`, `saints_maurice_lazare`, `medaille_militaire`, `medaille_coloniale`, `croix_rouge`. |
| `order_country` | string | Awarding state. The split between French and Tunisian (beylical) honours is the useful one: it separates recognition by the metropole from recognition by the Bey's government. |
| `grade` | categorical | `chevalier` < `officier` < `commandeur` < `grand_officier` < `grand_croix` / `grand_cordon` / `grand_maitre`; plus `medaille`, `titulaire`, or empty where no grade is printed (16%). |
| `context` | string | ±45 characters around the match, so any coding can be checked at a glance. |

`palmes_academiques` merges the two titles of the same order — *officier
d'Académie* (lower) and *officier de l'Instruction publique* (higher). `context`
distinguishes them.

Honours are matched with an edit-distance tolerance on a closed vocabulary,
because the OCR renders "Nichan-Iftikhar" a dozen different ways. This buys
recall at some cost in precision; `context` is there to audit it.

---

## career_positions.csv

The SUCCESS' rubric split into its posts, in printed order.

| variable | type | definition |
|---|---|---|
| `entry_id`, `surname` | string | Person. |
| `position_order` | integer | Sequence position, 1 = first post listed. Lambert lists posts chronologically, so this is a career ordering even where dates are missing. |
| `position_raw` | string | The verbatim segment. |
| `year_first_mentioned` | integer | First year in the segment, if any. |
| `place_mentioned` | string | First "à <Place>" in the segment. |
| `occupation_categories` | string | Categories matched in this post specifically — this is what makes career *trajectories* codeable (e.g. military → administration). |

---

## education.csv

| variable | type | definition |
|---|---|---|
| `entry_id`, `surname` | string | Person. |
| `institution` | string | Institution named in the ETUDES rubric. |
| `institution_kind` | categorical | `university_faculty`, `grande_ecole`, `teacher_training`, `secondary_lycee`, `secondary_college`, `islamic_institution` (Khaldounia, Grande Mosquée/Zitouna, Collège Sadiki), `technical_school`, `institute`, `other`. |
| `degrees` | string | The person's degrees, repeated for convenience. |

---

## mentions.csv

Every person named inside someone else's entry, before any tie is built. This is
the audit table for name resolution.

| variable | type | definition |
|---|---|---|
| `mention_id` | string | Key. |
| `source_entry_id`, `source_entry_type` | string | The entry the name was found in. |
| `name_raw` | string | The name as extracted from the list. |
| `name_key` | string | Normalised comparison key. |
| `role` | categorical | Role attached to the name (see the role list below), or `property_owner`. |
| `person_entry_id` | string | The matched person, if resolution succeeded. |
| `resolution` | categorical | `resolved` (exactly one person with an entry carries that surname), `resolved_fuzzy` (one match within one character — an OCR tolerance), `ambiguous` / `ambiguous_fuzzy` (more than one candidate: **no tie is assigned**), `unmatched` (nobody with an entry carries the name). |
| `n_candidates` | integer | Candidates found. |
| `page`, `page_url` | | Where to check it. |
| `evidence` | string | Up to 180 characters of the surrounding list. |

`unmatched` is the majority case and is not an error: the volume names far more
people in its officer lists than it gives notices to. They are kept in the
network as `person_named_only` nodes.

---

## edges_person_organisation.csv

The affiliation network, two-mode.

| variable | type | definition |
|---|---|---|
| `person_node` | string | `entry_id` where the person has a notice; otherwise `NAME:<key>`. |
| `person_name`, `person_entry_id`, `resolution` | | As in `mentions.csv`. |
| `organisation_node` | string | `entry_id` where the body has a notice; otherwise `ORG:<key>`. |
| `organisation_name`, `organisation_name_raw` | string | Canonical and as-found names. Variants are merged only when one's distinctive tokens are a subset of the other's and at least two are shared. |
| `role` | categorical | `president`, `honorary_president`, `past_president`, `vice_president`, `honorary_vice_president`, `secretary`, `secretary_general`, `deputy_secretary`, `treasurer`, `deputy_treasurer`, `assessor`, `board_member`, `councillor`, `commissioner`, `delegate`, `director`, `founder`, `archivist_librarian`, `honorary_member`, `member`, `corresponding_member`, `auditor`, `rapporteur`. |
| `tie_source` | categorical | `organisation_entry_officer_list` (n = 968) or `person_entry_statement` (n = 793). The first is a printed list of officers; the second is the person's own claim in their notice. They are not equally reliable and should be modelled separately or with a fixed effect. |
| `organisation_founded_year` | integer | Where the body has an entry. |
| `page`, `page_url`, `evidence` | | Verification. |

**No tie is dated.** Lambert prints the state of affairs around 1911–12; officer
lists are current at publication, while `person_entry_statement` ties may refer
to any point in a career ("membre de la Chambre de Commerce de 1898 à 1902").
This is a cross-section, not a panel.

## edges_person_place.csv

| variable | type | definition |
|---|---|---|
| `person_node`, `person_name`, `person_entry_id`, `resolution` | | As above. |
| `place_node` | string | `entry_id` where the place has a notice; otherwise `PLACE:<key>`. |
| `place_name` | string | |
| `relation` | categorical | `property_owner` (named in a locality's owner list), `residence` (city of the address), `birthplace`. |
| `controle_civil` | string | For `property_owner` ties. |
| `page`, `page_url`, `evidence` | | Verification. |

## edges_person_person.csv

One-mode projection: two people sharing an organisation.

| variable | type | definition |
|---|---|---|
| `source`, `target` | string | Person node ids, sorted, undirected. |
| `weight` | integer | Number of organisations shared. |
| `edge_type` | constant | `co_membership`. |
| `shared_organisations` | string | Semicolon-separated organisation node ids. |

Bodies with more than 60 recorded members are excluded from the projection: a
membership roll of several hundred is not evidence that any two names on it knew
each other. Note that this projection is a derived convenience — the two-mode
edge list is the primary object, and most affiliation-network methods should be
run on that instead.

## person_network_measures.csv

Each person's position in the two networks, so that network structure can be
used as a variable without rebuilding the graphs. One row per person node
appearing in either network — 1,134 nodes, of which 556 have a notice of their
own and the rest are people named only inside someone else's entry.

| variable | type | definition |
|---|---|---|
| `node_id` | string | Person node id, joins to `network_nodes.csv`. |
| `label` | string | Display name. |
| `entry_id` | string | The person's own notice, blank if they have none. |
| `has_notice` | 0/1 | Whether `entry_id` is filled. |
| `affil_degree` | integer | Distinct bodies the person is recorded in. |
| `affil_component_size` | integer | Nodes in their component of the two-mode graph, people *and* bodies. |
| `affil_in_giant` | 0/1 | Whether that component is the largest. |
| `affil_betweenness` | float | Normalised betweenness within their component. |
| `affil_closeness` | float | Closeness (Wasserman–Faust) within their component. |
| `comem_degree` | integer | Distinct people they share a body with. |
| `comem_component_size` | integer | Nodes in their component of the projection. |
| `comem_in_giant` | 0/1 | Whether that component is the largest (745 nodes). |
| `comem_betweenness` | float | Normalised betweenness within their component. |
| `comem_closeness` | float | Closeness within their component. |
| `comem_clustering` | float | Local clustering coefficient. |

Four things to know before using these columns.

**`affil_` and `comem_` are different graphs.** `affil_` is the two-mode people ×
bodies network, where paths run person → body → person, so betweenness measures
brokerage *between organisations*. `comem_` is the one-mode projection, which is
the graph the comparison tables model; its giant-component values are identical
to the ones that stage computes.

**Every measure is computed inside the node's own component**, because
centrality is undefined across components. `*_component_size` is exported so
that comparing a score from a three-node component with one from the giant — a
meaningless comparison — is at least a visible one. Most uses should filter on
`*_in_giant`.

**Blank is not zero.** A person absent from a network has no score there; a
person present in it with a score of 0 brokers nothing. The file keeps the two
apart, and so should any analysis: reading blanks as zeros invents 578 people
with measured-but-null positions.

**No `affil_clustering`.** A two-mode graph has no triangles, so it would be
zero for every row.

Both graphs are taken exactly as the published edge lists give them. Ties
resolved only ambiguously are included, as they are in those files and in the
comparison tables. The betweenness *figures* additionally drop
generically-named organisation nodes — see `code/figures/_networks.py` — and
that filter is deliberately not applied here, so this table stays a faithful
function of its inputs rather than of a figure's editorial choice.

## network_nodes.csv / network_edges.csv

A single node and edge table for Gephi, igraph, or NetworkX, combining the
person-organisation and person-place edges.

`network_nodes.csv`: `node_id`, `label`, `node_type` (`person_with_entry`,
`person_named_only`, `organisation_with_entry`, `organisation_named_only`,
`place_with_entry`, `place_named_only`), `subtype` (occupation, organisation
kind, or *contrôle civil* as appropriate), `birth_year` (or foundation year),
`n_decorations`, `has_portrait`, `entry_length_chars`, `page`, `page_url`.

`network_edges.csv`: `source`, `target`, `edge_type` (`affiliation`,
`property_owner`, `residence`, `birthplace`), `role`, `weight`, `tie_source`,
`resolution`, `page`, `page_url`.

The node table includes every entity, including isolates, so that non-membership
is observable rather than missing.


---

## The interpretive layer: person_communities.csv and person_gender.csv

These two tables differ in kind from everything above. The rest of the dataset
transcribes what the page says; these two **code what the page implies**. They
are kept in separate files, joined by `entry_id`, so that the transcription can
be used without them and so that anyone who disagrees with the coding can
replace it without touching the rest.

Three rules hold in both:

1. **Evidence over inference.** Each row carries an `evidence` column naming the
   rules that fired, and a confidence. A researcher can restrict to `high`, or
   re-code from the evidence, without re-running anything.
2. **Silence stays silent.** Where the volume prints nothing diagnostic the value
   is `unknown` / `UNKNOWN` — 37% of community codings and 14% of gender
   codings. That share is not a defect to be imputed away.
3. **Nobody is classified from a surname.** Surname-based ethnic attribution is
   the standard way this coding goes wrong, and in Tunisia it goes wrong
   predictably: Cardoso, Valensi, Lumbroso and Bessis are borne by Tunisian
   Jewish and Italian Catholic families alike.

### person_communities.csv

| variable | type | definition |
|---|---|---|
| `entry_id`, `surname`, `forenames` | string | Join key and name. |
| `community` | categorical | `european_french`, `european_italian`, `european_maltese`, `european_other`, `tunisian_muslim`, `tunisian_jewish`, `unknown`. |
| `community_group` | categorical | `european`, `tunisian`, `unknown`. |
| `confidence` | categorical | `high` (an institution the person held office in or attended, or a birthplace outside Tunisia), `medium` (a community body they belonged to, an Algerian birth, an Arabic patronymic in the printed name), `low` (competing evidence, or a French settler body alone). |
| `evidence` | string | Semicolon-separated rules that fired: `muslim_office`, `islamic_school`, `jewish_institution`, `described_israelite`, `italian_institution`, `maltese_marker`, `member_of:*_body`, `birth_france`, `birth_italy`, `birth_algeria`, `birth_malta`, `birth_tunisia`, `nasab_particle`, `honorific`, `livorno_jewish_note`. |
| `competing_categories` | string | Other categories the evidence also supported. Non-empty for 70 rows. |

**The categories are the volume's own.** Lambert's *Israélites* entry calls Jews
"une partie importante de la population indigène", and his *Tunisiens* entry
records that "Tunisiens" was what the country's Jews called themselves. That
1912 usage is why Jews sit on the Tunisian side here. It is not a claim about
nationality, which for many people in this book was separate and contested.

**Hard cases, handled explicitly.** Livornese Jews (the Grana) held Italian
nationality and a Tunisian communal life; religious evidence outranks birthplace,
so they code `tunisian_jewish` and carry `livorno_jewish_note`. Algeria-born
people with no other marker code `european_french` at medium confidence, flagged
`birth_algeria`. People born in Tunisia with no other marker stay `unknown`,
flagged `birth_tunisia` — a Tunis birth fits all three communities, second-
generation settlers included, and it is the single largest reason a row is not
classified.

### person_gender.csv

| variable | type | definition |
|---|---|---|
| `entry_id`, `surname`, `forenames` | string | Join key and name. |
| `gender` | categorical | `MALE` (1,115), `FEMALE` (11), `UNKNOWN` (181). |
| `gender_confidence` | categorical | `high` (civil title, "née", feminine occupational noun), `medium` (forename or grammatically gendered occupation), `low` (conflicting). |
| `gender_evidence` | string | `civil_title`, `nee_participle`, `feminine_occupation`, `masculine_occupation`, `feminine_forename`, `masculine_forename`. |
| `community`, `community_group` | categorical | Joined from `person_communities.csv` for convenience. |

All eleven women were checked individually against the page image. Two coding
traps are worth naming, because both produced false positives in a first pass:
*"école primaire supérieure"* carries feminine agreement with the school, not the
person, and the OCR renders both "Mme" and *Maître* as `M` plus punctuation, so
"Secrétaire de Mᵉ Gueydan" is one man working for another. The rules now require
a civil title to sit inside the subject's own parenthesis.
