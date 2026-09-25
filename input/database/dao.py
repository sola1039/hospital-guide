# -*- coding: utf-8 -*-
"""SQLite 数据访问封装。所有模块统一从这里读写数据, 不各自拼 SQL。"""
import os
import sqlite3
from typing import Any, Optional

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE, "input", "database", "hospital.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: tuple = ()) -> list:
    conn = get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def insert(sql: str, params: tuple = ()) -> None:
    execute(sql, params)


# ---------- 科室 ----------

def list_departments(floor: Optional[int] = None, category: Optional[str] = None) -> list:
    sql = "SELECT * FROM departments WHERE 1=1"
    args: list = []
    if floor is not None:
        sql += " AND floor = ?"
        args.append(floor)
    if category is not None:
        sql += " AND category = ?"
        args.append(category)
    sql += " ORDER BY floor, id"
    return query(sql, tuple(args))


def get_department(dept_id: str) -> Optional[dict]:
    return query_one("SELECT * FROM departments WHERE id = ?", (dept_id,))


def search_departments(keyword: str) -> list:
    """按名称/别名模糊匹配科室, 供导诊用。"""
    kw = f"%{keyword}%"
    return query(
        "SELECT * FROM departments WHERE name LIKE ? OR aliases LIKE ? ORDER BY floor",
        (kw, kw),
    )


# ---------- 须知 ----------

def list_exam_prep() -> list:
    return query("SELECT * FROM exam_prep ORDER BY id")


def search_exam_prep(keyword: str) -> list:
    kw = f"%{keyword}%"
    return query("SELECT * FROM exam_prep WHERE exam_name LIKE ? OR prep_text LIKE ?", (kw, kw))


def list_medicine_guide() -> list:
    return query("SELECT * FROM medicine_guide ORDER BY category, id")


# ---------- 医生与挂号演示 ----------

def list_doctors(dept_id: Optional[str] = None) -> list:
    if dept_id is None:
        return query("SELECT * FROM doctors_demo ORDER BY dept_id, id")
    return query("SELECT * FROM doctors_demo WHERE dept_id = ? ORDER BY id", (dept_id,))


def get_doctor(doctor_id: str) -> Optional[dict]:
    return query_one("SELECT * FROM doctors_demo WHERE id = ?", (doctor_id,))


def create_registration(reg_id: str, patient_name: str, doctor_id: str, dept_id: str,
                        visit_date: str, slot: str, created_at: str) -> None:
    insert(
        "INSERT INTO registrations_demo (id, patient_name, doctor_id, dept_id, visit_date, slot, status, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (reg_id, patient_name, doctor_id, dept_id, visit_date, slot, "已预约", created_at),
    )


def list_registrations(patient_name: Optional[str] = None) -> list:
    if patient_name is None:
        return query("SELECT * FROM registrations_demo ORDER BY created_at DESC")
    return query(
        "SELECT * FROM registrations_demo WHERE patient_name = ? ORDER BY created_at DESC",
        (patient_name,),
    )


# ---------- 导航 ----------

def get_nav_graph(floor: int) -> dict:
    nodes = query("SELECT * FROM nav_nodes WHERE floor = ? ORDER BY id", (floor,))
    edges = query("SELECT node_a, node_b, weight FROM nav_edges WHERE floor = ?", (floor,))
    return {"floor": floor, "nodes": nodes, "edges": edges}


def get_vertical_links() -> list:
    return query("SELECT * FROM vertical_links ORDER BY group_name, floor")


def find_nav_node(node_id: str) -> Optional[dict]:
    return query_one("SELECT * FROM nav_nodes WHERE id = ?", (node_id,))


def find_nodes_by_name(keyword: str) -> list:
    kw = f"%{keyword}%"
    return query("SELECT * FROM nav_nodes WHERE name LIKE ? ORDER BY floor, id", (kw,))


# ---------- 会话与对话记录 ----------

def create_session(session_id: str, state_json: str, created_at: str) -> None:
    insert("INSERT INTO sessions (id, created_at, state_json) VALUES (?,?,?)",
           (session_id, created_at, state_json))


def update_session_state(session_id: str, state_json: str) -> None:
    execute("UPDATE sessions SET state_json = ? WHERE id = ?", (state_json, session_id))


def get_session(session_id: str) -> Optional[dict]:
    return query_one("SELECT * FROM sessions WHERE id = ?", (session_id,))


def save_chat(session_id: str, role: str, content: str, created_at: str) -> None:
    insert("INSERT INTO chat_logs (session_id, role, content, created_at) VALUES (?,?,?,?)",
           (session_id, role, content, created_at))


def get_chat_logs(session_id: str, limit: int = 50) -> list:
    return query(
        "SELECT * FROM chat_logs WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
