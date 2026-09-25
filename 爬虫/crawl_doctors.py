# 主爬虫: 科室团队页 -> 医生详情页, 断点续传, 输出 Temp/doctors_raw.json
import json
import sys
import time
from pathlib import Path

from crawler_core import BASE, SiteSession
from parser import collect_team_ids, parse_doctor_page, parse_team_page

ROOT = Path(__file__).parent
TMP = ROOT / "Temp"
CHECKPOINT = TMP / "checkpoint.json"
RAW_OUT = TMP / "doctors_raw.json"
SEED_URL = BASE + "/Html/Hospitals/Doctors/Overview111.html"


def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        data["raw"] = {int(k): v for k, v in data.get("raw", {}).items()}
        return data
    return {"done_teams": [], "done_doctors": [], "raw": {}}


def save_checkpoint(state: dict) -> None:
    CHECKPOINT.write_text(
        json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def main() -> None:
    state = load_checkpoint()
    done_teams = set(state["done_teams"])
    done_doctors = set(state["done_doctors"])
    raw = state["raw"]
    session = SiteSession()
    try:
        seed = session.get_html(SEED_URL)
        team_ids = sorted(collect_team_ids(seed))
        print(f"科室团队页共 {len(team_ids)} 个")
        pending_teams = [t for t in team_ids if t not in done_teams]
        print(f"待抓团队页 {len(pending_teams)} 个")

        for i, team_id in enumerate(pending_teams, 1):
            url = f"{BASE}/Html/Departments/Main/DoctorTeam_{team_id}.html"
            try:
                html = session.get_html(url)
            except RuntimeError as e:
                print(f"[跳过] 团队页 {team_id}: {e}")
                continue
            entries = parse_team_page(html)
            for ent in entries:
                doc_id = ent.pop("id")
                if doc_id not in raw:
                    raw[doc_id] = {
                        "id": doc_id,
                        "姓名": ent["姓名"],
                        "职称": ent["职称"],
                        "科室": "",
                        "职务": "",
                        "诊疗特长": ent.get("特长", ""),
                        "详细介绍": "",
                        "来源": f"{BASE}/Html/Doctors/Main/Index_{doc_id}.html",
                    }
            done_teams.add(team_id)
            state["done_teams"] = sorted(done_teams)
            state["raw"] = raw
            save_checkpoint(state)
            print(f"[{i}/{len(pending_teams)}] 团队页 {team_id}: {len(entries)} 人")
            time.sleep(0.8)

        pending_docs = [d for d in sorted(raw) if d not in done_doctors]
        print(f"医生详情页共 {len(pending_docs)} 个待抓")

        for i, doc_id in enumerate(pending_docs, 1):
            url = raw[doc_id]["来源"]
            try:
                html = session.get_html(url, min_len=4000)
                info = parse_doctor_page(html)
                rec = raw[doc_id]
                raw[doc_id] = {
                    "id": doc_id,
                    "姓名": info["姓名"] or rec["姓名"],
                    "职称": info["职称"] or rec["职称"],
                    "科室": info["科室"] or rec["科室"],
                    "职务": info["职务"],
                    "诊疗特长": info["诊疗特长"] or rec["诊疗特长"],
                    "详细介绍": info["详细介绍"],
                    "来源": url,
                }
            except RuntimeError as e:
                print(f"[跳过] 医生 {doc_id}: {e}")
            done_doctors.add(doc_id)
            state["done_doctors"] = sorted(done_doctors)
            state["raw"] = raw
            save_checkpoint(state)
            if i % 20 == 0 or i == len(pending_docs):
                print(f"[{i}/{len(pending_docs)}] 医生详情抓取中")
            time.sleep(0.6)

        RAW_OUT.write_text(
            json.dumps(list(raw.values()), ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"完成: 共 {len(raw)} 名医生 -> {RAW_OUT}")
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
