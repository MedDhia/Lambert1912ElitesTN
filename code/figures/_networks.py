"""Graph construction shared by the betweenness figures.

One script per figure is the rule, but the decision about *which* nodes are
admissible is a data judgement rather than a drawing one, and four figures rest
on it. Repeating it four times would let the four drift apart, so it lives here.

## Why some organisation nodes are excluded

Betweenness counts shortest paths, so a node that wrongly merges two distinct
bodies does not merely add noise: it invents a path between people who were
never connected, and then scores highly for sitting on it.

The dataset has a handful of such nodes. When a person's entry names a body
without giving its full title, `build_networks.py` creates a synthetic node
keyed on the printed string (`ORG:...`). Usually that string is specific enough
to identify one body. Sometimes it is a bare common noun — "Société",
"Municipalité", "Chambre d'Agriculture" — and every person who wrote it lands on
the same node. `ORG:societe` carried 12 ties printed on 12 different pages, and
scored the fourth-highest betweenness in the whole network on the strength of
paths that do not exist. Tunisia had many municipalities and several chambers of
agriculture; the volume names them without qualification and the coder cannot
tell them apart.

The rule below drops a node when *both* hold:

1. it has no dictionary entry of its own (the id starts with `ORG:`), and
2. every word in its name, articles and prepositions aside, is a generic
   institutional noun.

Condition 1 does the real work. A body with its own entry is a body Lambert
identified, so "Conférence Consultative" and "Cercle Tunisien" are kept however
generic they read — they are single, named institutions. Condition 2 then spares
the specific `ORG:` nodes: "Touring-Club", "Société Franc-Comtoise", "Institut de
Carthage et la Société de Géographie commerciale de Paris" all survive, because
each carries at least one word that is not boilerplate.

This removes 16 nodes and 48 of 1,217 ties — about 4% — and it is a deliberately
conservative cut. It is applied only to the betweenness figures, where a false
bridge is actively misleading. Figures 14, 15 and 25 draw the unfiltered graph;
their measure is degree, which a merged node inflates only locally.
"""

from __future__ import annotations

import re

import networkx as nx

import _style as S

GENERIC_WORDS = {
    "societe", "société", "municipalite", "municipalité", "institut", "conseil",
    "tribunal", "chambre", "comite", "comité", "cercle", "association", "ligue",
    "syndicat", "club", "gymnastique", "agriculture", "commerce", "direction",
    "bureau", "administration", "ecole", "école", "hopital", "hôpital",
    "mutuelle", "union", "federation", "fédération", "amicale", "cie",
    "compagnie",
}
_ARTICLES = {"de", "du", "des", "la", "le", "les", "l", "d", "et", "en", "a", "à"}


def is_unidentifiable(node_id: str, name: str) -> bool:
    """True for a synthetic node whose printed name names no particular body."""
    if not node_id.startswith("ORG:"):
        return False  # it has its own dictionary entry, so Lambert identified it
    words = [w for w in re.split(r"[\s'’\-]+", name.lower()) if w and w not in _ARTICLES]
    return bool(words) and all(w in GENERIC_WORDS for w in words)


def affiliation_graph() -> tuple[nx.Graph, dict[str, str], int]:
    """The two-mode people × bodies graph, minus the unidentifiable bodies.

    Returns the graph, a node -> display label map, and the number of ties the
    exclusion rule dropped (so a figure can state it on its face).
    """
    graph = nx.Graph()
    labels: dict[str, str] = {}
    dropped = 0
    for tie in S.read("edges_person_organisation.csv"):
        if tie["resolution"].startswith("ambiguous"):
            continue  # a surname shared by two people assigns no tie
        if is_unidentifiable(tie["organisation_node"], tie["organisation_name"]):
            dropped += 1
            continue
        graph.add_node(tie["person_node"], kind="person")
        graph.add_node(tie["organisation_node"], kind="org")
        labels[tie["person_node"]] = tie["person_name"]
        labels[tie["organisation_node"]] = tie["organisation_name"]
        graph.add_edge(tie["person_node"], tie["organisation_node"])
    return graph, labels, dropped


def comembership_graph() -> nx.Graph:
    """The one-mode projection: an edge wherever two people share a body."""
    graph = nx.Graph()
    for pair in S.read("edges_person_person.csv"):
        graph.add_edge(pair["source"], pair["target"], weight=int(pair["weight"]))
    return graph


def giant(graph: nx.Graph) -> nx.Graph:
    return graph.subgraph(max(nx.connected_components(graph), key=len)).copy()


def ranked(scores: dict[str, float], among=None, n: int | None = None) -> list[str]:
    """Nodes ordered by score, highest first, with ties broken by node id.

    Every "top N brokers" list in these figures comes through here, because
    getting this wrong is not a cosmetic bug.

    Betweenness ties are common at the low end and do occur among the leaders:
    two people in the affiliation network hold four ties each and score
    identically. Ordering them by anything the interpreter is free to vary --
    a set's iteration order, or `sorted` with no tiebreak over a dict built in
    a varying order -- means a caption naming "the broker holding fewest ties"
    can name a different person on a rebuild. That happened: fig. 32 alternated
    between Nestler and Vendel across runs, each time stating it as fact.

    Sorting on `(-score, node_id)` is a total order over distinct nodes, so the
    result depends on nothing but the input values. Callers that need a further
    key (fig. 32 ranks by degree first) compose it the same way, ending in the
    node id.

    `among` optionally restricts the candidates; `n` truncates.
    """
    candidates = list(scores) if among is None else list(among)
    ordered = sorted(candidates, key=lambda node: (-scores[node], node))
    return ordered if n is None else ordered[:n]


def pretty(node: str, names: dict[str, str], labels: dict[str, str] | None = None) -> str:
    """A node's name as it should appear on a chart.

    People named only inside someone else's entry carry a synthetic `NAME:` id
    and are stored upper-cased with a forename slot that is often empty, so a
    raw label reads `DJEHANE ()`. Empty brackets are dropped rather than printed.
    """
    raw = names.get(node) or (labels or {}).get(node) or node
    raw = raw.replace("NAME:", "").strip()
    raw = re.sub(r"\(\s*\)", "", raw).strip()
    # Case-fold word by word rather than over the whole string. Surnames are
    # stored in caps and read better title-cased, but an organisation's name is
    # already mixed case and `str.title()` would wreck it ("Institut De Carthage
    # Et La ..."). Only fully-capitalised words are touched.
    return " ".join(w.title() if w.isupper() else w for w in raw.split())


def display_names() -> dict[str, str]:
    """Labels for every node, including people named only in someone else's entry."""
    return {n["node_id"]: n["label"] for n in S.read("network_nodes.csv")}


def person_communities() -> dict[str, str]:
    """Person node -> community group, via the entry id the tie file carries."""
    community = {r["entry_id"]: r["community_group"]
                 for r in S.read("person_communities.csv")}
    return {
        tie["person_node"]: community.get(tie["person_entry_id"], "unknown") or "unknown"
        for tie in S.read("edges_person_organisation.csv") if tie["person_entry_id"]
    }
