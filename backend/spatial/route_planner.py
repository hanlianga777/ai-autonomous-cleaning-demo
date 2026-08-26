"""A deterministic Dijkstra planner over the campus connector graph."""

from __future__ import annotations

import heapq
from collections import defaultdict

from spatial.spatial_data import GRAPH_EDGES, GRAPH_NODES


class RouteNotFoundError(ValueError):
    pass


def _adjacency() -> dict[str, list[tuple[str, int, str]]]:
    graph: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for source, target, cost, edge_type in GRAPH_EDGES:
        graph[source].append((target, cost, edge_type))
        graph[target].append((source, cost, edge_type))
    return graph


def plan_route(start_map: str, target_map: str) -> dict:
    if start_map not in GRAPH_NODES or target_map not in GRAPH_NODES:
        raise RouteNotFoundError("Unknown spatial map")
    if start_map == target_map:
        return {"start_map": start_map, "target_map": target_map, "total_cost": 0, "node_path": [start_map], "display_path": [GRAPH_NODES[start_map]["label"]], "segments": []}

    graph = _adjacency()
    queue: list[tuple[int, str]] = [(0, start_map)]
    distances = {start_map: 0}
    previous: dict[str, tuple[str, str, int]] = {}

    while queue:
        cost, node = heapq.heappop(queue)
        if node == target_map:
            break
        if cost != distances[node]:
            continue
        for neighbor, edge_cost, edge_type in graph[node]:
            candidate = cost + edge_cost
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = (node, edge_type, edge_cost)
                heapq.heappush(queue, (candidate, neighbor))

    if target_map not in previous:
        raise RouteNotFoundError(f"No route from {start_map} to {target_map}")

    node_path = [target_map]
    segments = []
    cursor = target_map
    while cursor != start_map:
        parent, edge_type, edge_cost = previous[cursor]
        segments.append({"from": parent, "to": cursor, "type": edge_type, "cost": edge_cost})
        node_path.append(parent)
        cursor = parent
    node_path.reverse()
    segments.reverse()

    display_path: list[str] = []
    for node in node_path:
        label = GRAPH_NODES[node]["label"]
        if not display_path or display_path[-1] != label:
            display_path.append(label)
    return {"start_map": start_map, "target_map": target_map, "total_cost": distances[target_map], "node_path": node_path, "display_path": display_path, "segments": segments}
