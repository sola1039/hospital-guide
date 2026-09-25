# -*- coding: utf-8 -*-
"""院内导航接口: 起终点解析 + 寻路 + POI 查询。"""
from typing import Optional

from fastapi import APIRouter, HTTPException

import dao
from graph import NavGraph
from pathfinder import find_route

router = APIRouter()

_graph: Optional[NavGraph] = None


def get_graph() -> NavGraph:
    """路网图只构建一次, 供所有请求复用。"""
    global _graph
    if _graph is None:
        _graph = NavGraph.from_db()
    return _graph


def resolve_node(ref: str) -> Optional[str]:
    """把用户给的起点/终点(节点id/科室名/地点名)解析成路网节点 id。"""
    ref = (ref or "").strip()
    if not ref:
        return None
    node = dao.find_nav_node(ref)
    if node:
        return node["id"]
    dept = dao.get_department(ref)
    if dept:
        return dept["nav_node_id"]
    depts = dao.search_departments(ref)
    if depts:
        return depts[0]["nav_node_id"]
    nodes = dao.find_nodes_by_name(ref)
    if nodes:
        return nodes[0]["id"]
    return None


@router.get("/floors")
def list_floors() -> list:
    return dao.query("SELECT * FROM floors ORDER BY id")


@router.get("/pois")
def list_pois(floor: Optional[int] = None) -> list:
    if floor is None:
        return dao.query("SELECT * FROM nav_nodes ORDER BY floor, id")
    return dao.query("SELECT * FROM nav_nodes WHERE floor = ? ORDER BY id", (floor,))


@router.get("/navigate")
def navigate(start: str, end: str) -> dict:
    """寻路。start/end 可传节点id、科室名或地点名。"""
    start_id = resolve_node(start)
    end_id = resolve_node(end)
    if start_id is None:
        raise HTTPException(status_code=404, detail=f"找不到起点: {start}")
    if end_id is None:
        raise HTTPException(status_code=404, detail=f"找不到终点: {end}")
    route = find_route(get_graph(), start_id, end_id)
    if route is None:
        raise HTTPException(status_code=404, detail="起点与终点之间没有可用路线")
    return route


@router.get("/navigate/by-dept")
def navigate_to_dept(start: str, dept_id: str) -> dict:
    dept = dao.get_department(dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {dept_id}")
    return navigate(start, dept["nav_node_id"])
