# 组装最终交付数据: 医生信息.json (姓名/职称/科室/出诊时间/简介)
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
TMP = ROOT / "Temp"
RAW = TMP / "doctors_raw.json"
SCHEDULES = TMP / "schedules.json"
OUT = ROOT / "医生信息.json"
SCHEDULE_DEFAULT = "官网未公布,可查询健康160预约平台"
TITLE_ORDER = {"主任医师": 0, "副主任医师": 1, "主治医师": 2, "住院医师": 3}


def build_intro(rec: dict) -> str:
    parts = []
    if rec.get("诊疗特长"):
        parts.append(rec["诊疗特长"])
    if rec.get("详细介绍"):
        parts.append(rec["详细介绍"])
    return "\n\n".join(parts)


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    schedules = {}
    if SCHEDULES.exists():
        schedules = json.loads(SCHEDULES.read_text(encoding="utf-8"))

    out = []
    for rec in raw:
        out.append(
            {
                "姓名": rec["姓名"],
                "职称": rec["职称"],
                "科室": rec["科室"],
                "出诊时间": schedules.get(rec["姓名"], SCHEDULE_DEFAULT),
                "简介": build_intro(rec),
            }
        )

    out.sort(
        key=lambda r: (
            r["科室"],
            TITLE_ORDER.get(r["职称"], 9),
            r["姓名"],
        )
    )
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    empty_dept = sum(1 for r in out if not r["科室"])
    empty_intro = sum(1 for r in out if not r["简介"])
    print(f"输出 {len(out)} 条 -> {OUT}")
    print(f"缺科室 {empty_dept} 条, 缺简介 {empty_intro} 条")
    print(f"文件大小: {os.path.getsize(OUT)} 字节")


if __name__ == "__main__":
    main()
