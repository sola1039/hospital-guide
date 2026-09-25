# -*- coding: utf-8 -*-
"""Dijkstra 最短路寻路(移植自 simpleroutingsvg 的 shortestway 库)。

输出: 分楼层的路径段(像素坐标序列) + 面向老人的分步指引文字。
"""
import heapq
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph import NavGraph, PX_PER_METER, Node

# 垂直交通的动作文案
VERT_ACTION = {"elev": "乘电梯", "stair": "走楼梯", "escalator": "乘扶梯"}
VERT_TYPE = {"elev", "stair", "escalator"}


def dijkstra(graph: NavGraph, start_id: str, end_id: str) -> Optional[list]:
    """返回 start->end 的最短节点序列, 不可达返回 None。"""
    if start_id not in graph.nodes or end_id not in graph.nodes:
        return None
    dist = {start_id: 0.0}
    prev: dict = {}
    pq = [(0.0, start_id)]
    visited = set()
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in visited:
            continue
        visited.add(cur)
        if cur == end_id:
            break
        for nxt, w in graph.neighbors(cur):
            nd = d + w
            if nd < dist.get(nxt, float("inf")):
                dist[nxt] = nd
                prev[nxt] = cur
                heapq.heappush(pq, (nd, nxt))
    if end_id not in dist:
        return None
    path = [end_id]
    while path[-1] != start_id:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def find_route(graph: NavGraph, start_id: str, end_id: str) -> Optional[dict]:
    """寻路并生成面向用户的路线说明。"""
    path = dijkstra(graph, start_id, end_id)
    if path is None:
        return None
    nodes = [graph.nodes[nid] for nid in path]

    # 按楼层切分成路径段
    segments = []
    current = {"floor": nodes[0].floor, "points": [], "node_ids": []}
    for i, node in enumerate(nodes):
        if node.floor != current["floor"]:
            segments.append(current)
            current = {"floor": node.floor, "points": [], "node_ids": []}
        current["points"].append([node.x, node.y])
        current["node_ids"].append(node.id)
    segments.append(current)

    steps = _build_steps(nodes)
    total_px = 0.0
    for i in range(1, len(path)):
        total_px += _edge_weight(graph, path[i - 1], path[i])
    return {
        "start": _node_brief(nodes[0]),
        "end": _node_brief(nodes[-1]),
        "distance_px": round(total_px, 1),
        "distance_m": round(total_px / PX_PER_METER, 1),
        "segments": segments,
        "steps": steps,
    }


def _edge_weight(graph: NavGraph, a: str, b: str) -> float:
    for nxt, w in graph.neighbors(a):
        if nxt == b:
            return w
    return 0.0


def _node_brief(node: Node) -> dict:
    return {"id": node.id, "name": node.name, "floor": node.floor, "type": node.type, "x": node.x, "y": node.y}


def _build_steps(nodes: list) -> list:
    """把节点序列翻译成大白话步骤。"""
    steps = []
    walk_start = nodes[0]
    walk_dist = 0.0

    def flush_walk():
        nonlocal walk_dist
        if walk_dist > 5:
            meters = round(walk_dist / PX_PER_METER)
            steps.append({
                "kind": "walk", "floor": walk_start.floor,
                "text": f"从{walk_start.name}步行约{meters}米",
            })

    for i in range(1, len(nodes)):
        prev, cur = nodes[i - 1], nodes[i]
        seg_len = ((prev.x - cur.x) ** 2 + (prev.y - cur.y) ** 2) ** 0.5
        if prev.floor != cur.floor:
            flush_walk()
            action = VERT_ACTION.get(prev.type, "换层")
            steps.append({
                "kind": prev.type, "floor": cur.floor,
                "text": f"在{prev.name}{action}到{cur.floor}楼",
            })
            walk_start = cur
            walk_dist = 0.0
        else:
            walk_dist += seg_len
    flush_walk()
    steps.append({"kind": "arrive", "floor": nodes[-1].floor, "text": f"到达{nodes[-1].name}"})
    return steps
