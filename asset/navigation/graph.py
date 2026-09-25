# -*- coding: utf-8 -*-
"""路网图构建: 从数据库读取节点/边/垂直交通, 组装成统一的跨楼层图。"""
import math
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "database"))
import dao


@dataclass(frozen=True)
class Node:
    id: str
    floor: int
    x: int
    y: int
    type: str
    name: str
    link_group: str = ""


# 跨楼层垂直交通的通行代价(像素当量), 电梯最快, 楼梯最慢
VERT_COST = {"elev": 220.0, "escalator": 260.0, "stair": 320.0}
# 估算: 平面图 10 像素约等于 1 米
PX_PER_METER = 10.0


@dataclass
class NavGraph:
    nodes: dict = field(default_factory=dict)
    adj: dict = field(default_factory=dict)

    @classmethod
    def from_db(cls) -> "NavGraph":
        g = cls()
        for floor in (1, 2, 3, 4):
            data = dao.get_nav_graph(floor)
            for n in data["nodes"]:
                g.nodes[n["id"]] = Node(
                    id=n["id"], floor=n["floor"], x=n["x"], y=n["y"],
                    type=n["type"], name=n["name"], link_group=n.get("link_group") or "",
                )
            for e in data["edges"]:
                g.add_walk_edge(e["node_a"], e["node_b"], e["weight"])
        g._link_vertical()
        return g

    def add_walk_edge(self, a: str, b: str, weight: float) -> None:
        self.adj.setdefault(a, []).append((b, weight))
        self.adj.setdefault(b, []).append((a, weight))

    def _link_vertical(self) -> None:
        """同组垂直交通节点两两相连: 电梯/楼梯可达任意楼层, 扶梯只连相邻楼层。"""
        groups = {}
        for row in dao.get_vertical_links():
            groups.setdefault(row["group_name"], {"kind": row["kind"], "members": []})
            groups[row["group_name"]]["members"].append((row["floor"], row["node_id"]))
        for info in groups.values():
            kind = info["kind"]
            members = sorted(info["members"])
            for i, (fa, na) in enumerate(members):
                for fb, nb in members[i + 1:]:
                    if kind == "escalator" and abs(fa - fb) > 1:
                        continue
                    cost = VERT_COST.get(kind, 300.0) * abs(fa - fb)
                    self.add_walk_edge(na, nb, cost)

    def neighbors(self, node_id: str):
        return self.adj.get(node_id, [])

    def get(self, node_id: str):
        return self.nodes.get(node_id)


def pixel_distance(a: Node, b: Node) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)
