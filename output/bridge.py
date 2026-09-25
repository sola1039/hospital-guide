# -*- coding: utf-8 -*-
"""output 层预留透传接口: 把系统产出交给"下一个模块"。

透传方式(二选一或同时):
1. 落盘: 每条产出写入 output/outbox/ 目录, 下一模块直接读文件;
2. 推送: 设置环境变量 NEXT_MODULE_ENDPOINT 后, 每条产出以 JSON POST 到该地址。

事件类型与载荷结构见同目录 接口约定.md。
"""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX = os.path.join(BASE, "output", "outbox")


def forward(event_type: str, payload: dict) -> dict:
    """透传一条产出事件, 返回落盘路径与推送结果。"""
    os.makedirs(OUTBOX, exist_ok=True)
    record = {
        "event": event_type,
        "time": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    filename = f"{record['time'].replace(':', '-')[:19]}_{event_type}.json"
    path = os.path.join(OUTBOX, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)

    endpoint = os.environ.get("NEXT_MODULE_ENDPOINT", "")
    pushed = False
    if endpoint:
        pushed = _post(endpoint, record)
    return {"saved": path, "pushed": pushed}


def _post(endpoint: str, record: dict) -> bool:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(record, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
