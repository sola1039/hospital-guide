# -*- coding: utf-8 -*-
"""初始化 SQLite 数据库: 建表 + 导入路网标注 + 灌入种子数据。

用法: python input/database/init_db.py
可重复执行(每次重建表), 换医院时替换 input/data_source/ 与 seed_data.py 即可。
"""
import json
import os
import sqlite3

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE, "input", "database", "hospital.db")
SCHEMA_PATH = os.path.join(BASE, "input", "database", "schema.sql")
NAV_DIR = os.path.join(BASE, "input", "data_source", "nav_data")

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seed_data import DEPARTMENTS, EXAM_PREP, MEDICINE_GUIDE, DOCTORS_DEMO, DEPT_CRAWL_MAP

DOCTORS_CRAWLED_PATH = os.path.join(BASE, "input", "data_source", "doctors_crawled.json")


def load_doctors() -> list:
    """优先用爬虫抓取的真实医生数据, 缺失时退回演示数据。"""
    if not os.path.exists(DOCTORS_CRAWLED_PATH):
        return DOCTORS_DEMO
    with open(DOCTORS_CRAWLED_PATH, encoding="utf-8") as f:
        crawled = json.load(f)
    doctors = []
    for i, d in enumerate(crawled, 1):
        dept_id = DEPT_CRAWL_MAP.get((d.get("科室") or "").strip())
        if not dept_id:
            continue
        intro = (d.get("简介") or "").replace("\n", " ").strip()
        if len(intro) > 200:
            intro = intro[:200] + "..."
        doctors.append({
            "id": f"R{i:03d}",
            "name": (d.get("姓名") or "").strip(),
            "dept_id": dept_id,
            "title": (d.get("职称") or "").strip(),
            "schedule_text": (d.get("出诊时间") or "暂未公布").strip(),
            "intro": intro,
        })
    return doctors


def edge_weight(a: dict, b: dict) -> float:
    """边权 = 几何距离; 垂直交通按类型放大代价(爬楼比走路慢)。"""
    dist = ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
    factor = 1.0
    if a.get("type") in ("stair", "escalator") or b.get("type") in ("stair", "escalator"):
        factor = 1.5
    elif a.get("type") == "elev" or b.get("type") == "elev":
        factor = 1.2
    return round(dist * factor, 1)


def main() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    # 路网数据: input/data_source/nav_data/*.json -> nav_nodes/nav_edges/vertical_links
    node_types = {}
    for floor_no in range(1, 5):
        path = os.path.join(NAV_DIR, f"floor{floor_no}.json")
        with open(path, encoding="utf-8") as f:
            g = json.load(f)
        conn.execute(
            "INSERT INTO floors (id, name, image, width, height) VALUES (?,?,?,?,?)",
            (g["floor"], f"{g['floor']}F", g["image"], g["width"], g["height"]),
        )
        for n in g["nodes"]:
            node_types[n["id"]] = n
            conn.execute(
                "INSERT INTO nav_nodes (id, floor, x, y, type, name, link_group) VALUES (?,?,?,?,?,?,?)",
                (n["id"], g["floor"], n["x"], n["y"], n["type"], n["name"], n.get("link")),
            )
        for a, b in g["edges"]:
            conn.execute(
                "INSERT INTO nav_edges (node_a, node_b, floor, weight) VALUES (?,?,?,?)",
                (a, b, g["floor"], edge_weight(node_types[a], node_types[b])),
            )
    with open(os.path.join(NAV_DIR, "vertical_links.json"), encoding="utf-8") as f:
        links = json.load(f)
    for lg in links["links"]:
        for fl, nid in lg["members"].items():
            conn.execute(
                "INSERT INTO vertical_links (group_name, kind, label, floor, node_id) VALUES (?,?,?,?,?)",
                (lg["group"], lg["kind"], lg["label"], int(fl), nid),
            )

    # 种子数据
    for d in DEPARTMENTS:
        conn.execute(
            "INSERT INTO departments (id, name, floor, nav_node_id, category, intro, common_exams, tips, aliases) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (d["id"], d["name"], d["floor"], d["nav_node_id"], d["category"],
             d["intro"], d["common_exams"], d["tips"], d["aliases"]),
        )
    for e in EXAM_PREP:
        conn.execute(
            "INSERT INTO exam_prep (id, exam_name, fasting, duration, prep_text, keywords) VALUES (?,?,?,?,?,?)",
            (e["id"], e["exam_name"], e["fasting"], e["duration"], e["prep_text"], e.get("keywords", "")),
        )
    for m in MEDICINE_GUIDE:
        conn.execute(
            "INSERT INTO medicine_guide (id, category, title, content) VALUES (?,?,?,?)",
            (m["id"], m["category"], m["title"], m["content"]),
        )
    for doc in load_doctors():
        conn.execute(
            "INSERT INTO doctors_demo (id, name, dept_id, title, schedule_text, intro) VALUES (?,?,?,?,?,?)",
            (doc["id"], doc["name"], doc["dept_id"], doc["title"], doc["schedule_text"], doc["intro"]),
        )
    conn.commit()

    # 校验: 科室指向的导航节点必须存在
    orphans = conn.execute(
        "SELECT d.id, d.nav_node_id FROM departments d "
        "LEFT JOIN nav_nodes n ON d.nav_node_id = n.id WHERE n.id IS NULL"
    ).fetchall()
    counts = {
        "floors": conn.execute("SELECT COUNT(*) FROM floors").fetchone()[0],
        "nav_nodes": conn.execute("SELECT COUNT(*) FROM nav_nodes").fetchone()[0],
        "nav_edges": conn.execute("SELECT COUNT(*) FROM nav_edges").fetchone()[0],
        "departments": conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0],
        "exam_prep": conn.execute("SELECT COUNT(*) FROM exam_prep").fetchone()[0],
        "medicine_guide": conn.execute("SELECT COUNT(*) FROM medicine_guide").fetchone()[0],
        "doctors_demo": conn.execute("SELECT COUNT(*) FROM doctors_demo").fetchone()[0],
    }
    conn.close()
    size = os.path.getsize(DB_PATH)
    summary = " ".join(f"{k}={v}" for k, v in counts.items())
    print(f"初始化完成 {DB_PATH} ({size} bytes)")
    print(summary)
    if orphans:
        print("警告: 科室指向了不存在的路网节点:", orphans)
    else:
        print("科室路网节点校验通过")


if __name__ == "__main__":
    main()
