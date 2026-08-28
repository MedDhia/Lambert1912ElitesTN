"""Centrality measures for simple undirected graphs, standard library only.

The pipeline promises no third-party dependencies. `compare_populations.py`
quietly broke that promise: it imported networkx for four measures, so `make
all` -- the entry point the README gives -- failed with ModuleNotFoundError for
anyone who followed the README and installed nothing. CI never ran that stage,
so nothing caught it.

These functions reproduce the networkx results they replace *exactly*, on the
graph the comparison actually uses, and `tests/test_graph_metrics.py` pins that
against hand-worked examples with known values. Matching networkx to the last
float is what lets the committed comparison tables stay byte-identical, which is
the real check that this rewrite changed no finding.

Graphs are plain adjacency: `dict[node, set[node]]`, no self-loops, unweighted.
The co-membership projection is 745 nodes and 4,928 edges, so Brandes at O(nm)
is a few seconds of pure Python -- not worth a dependency.
"""

from __future__ import annotations

from collections import deque


def adjacency(edges) -> dict[str, set[str]]:
    """Build an undirected adjacency map from (source, target) pairs."""
    graph: dict[str, set[str]] = {}
    for source, target in edges:
        if source == target:
            continue  # a self-loop is not a tie between two people
        graph.setdefault(source, set()).add(target)
        graph.setdefault(target, set()).add(source)
    return graph


def components(graph: dict[str, set[str]]) -> list[set[str]]:
    """Connected components, largest first."""
    seen: set[str] = set()
    found: list[set[str]] = []
    for start in graph:
        if start in seen:
            continue
        component: set[str] = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in component:
                continue
            component.add(node)
            queue.extend(graph[node] - component)
        seen |= component
        found.append(component)
    # Sorted on (size, smallest member) so ties do not depend on set order.
    found.sort(key=lambda c: (-len(c), min(c)))
    return found


def giant_component(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    """The largest connected component, as a graph in its own right."""
    if not graph:
        return {}
    largest = components(graph)[0]
    return {node: graph[node] & largest for node in largest}


def betweenness(graph: dict[str, set[str]]) -> dict[str, float]:
    """Shortest-path betweenness, normalised as networkx does by default.

    Brandes (2001). Every shortest path is discovered twice in an undirected
    graph, once from each end, so the accumulated scores are halved before
    scaling by 1/((n-1)(n-2)) -- the number of ordered pairs excluding the node
    itself. The result matches `nx.betweenness_centrality(G)` exactly.
    """
    score = dict.fromkeys(graph, 0.0)
    for source in graph:
        stack: list[str] = []
        predecessors: dict[str, list[str]] = {node: [] for node in graph}
        paths = dict.fromkeys(graph, 0.0)
        paths[source] = 1.0
        distance = dict.fromkeys(graph, -1)
        distance[source] = 0
        queue = deque([source])
        while queue:
            node = queue.popleft()
            stack.append(node)
            for neighbour in graph[node]:
                if distance[neighbour] < 0:
                    distance[neighbour] = distance[node] + 1
                    queue.append(neighbour)
                if distance[neighbour] == distance[node] + 1:
                    paths[neighbour] += paths[node]
                    predecessors[neighbour].append(node)
        dependency = dict.fromkeys(graph, 0.0)
        while stack:
            node = stack.pop()
            for predecessor in predecessors[node]:
                dependency[predecessor] += (
                    paths[predecessor] / paths[node] * (1.0 + dependency[node]))
            if node != source:
                score[node] += dependency[node]

    n = len(graph)
    if n <= 2:
        return {node: 0.0 for node in graph}
    scale = 1.0 / ((n - 1) * (n - 2))
    return {node: value * scale for node, value in score.items()}


def closeness(graph: dict[str, set[str]]) -> dict[str, float]:
    """Closeness with the Wasserman-Faust correction, as networkx defaults to.

    For a node that reaches `r` others at total distance `total`, the value is
    `(r / total) * (r / (n - 1))`. On a connected graph the second factor is 1,
    which is the case here since callers pass the giant component.
    """
    n = len(graph)
    result: dict[str, float] = {}
    for source in graph:
        distance = {source: 0}
        queue = deque([source])
        total = 0
        while queue:
            node = queue.popleft()
            for neighbour in graph[node]:
                if neighbour not in distance:
                    distance[neighbour] = distance[node] + 1
                    total += distance[neighbour]
                    queue.append(neighbour)
        reached = len(distance) - 1
        if reached > 0 and total > 0:
            value = reached / total
            if n > 1:
                value *= reached / (n - 1)
            result[source] = value
        else:
            result[source] = 0.0
    return result


def clustering(graph: dict[str, set[str]]) -> dict[str, float]:
    """Local clustering coefficient: the share of a node's pairs that are tied.

    Zero for a node with fewer than two neighbours, where the coefficient is
    undefined and networkx also reports 0.
    """
    result: dict[str, float] = {}
    for node, neighbours in graph.items():
        degree = len(neighbours)
        if degree < 2:
            result[node] = 0.0
            continue
        links = sum(1 for a in neighbours for b in graph[a]
                    if b in neighbours and a < b)
        result[node] = 2.0 * links / (degree * (degree - 1))
    return result
