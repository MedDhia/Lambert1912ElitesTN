"""Deterministic ordering for the figures. Standard library only, on purpose.

This is separate from `_networks.py` so it can be imported without networkx or
matplotlib. The rule below is what keeps a caption from naming a different
person on a rebuild, which makes it worth testing in the ordinary test suite --
and that suite installs no plotting dependencies, so the rule cannot live in a
module that imports them.
"""

from __future__ import annotations

from collections.abc import Iterable


def ranked(scores: dict[str, float], among: Iterable[str] | None = None,
           n: int | None = None) -> list[str]:
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
