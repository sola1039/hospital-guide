# -*- coding: utf-8 -*-
"""就医引导引擎: 智能导诊 + 流程卡生成 + 对话编排。

分工: 状态机/知识库负责确定性流程, 大模型负责大白话解释与答疑。
大模型不可用时自动降级为知识库直答, 保证演示不中断。
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "input", "database"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dao
import llm_client
from process_kb import PROCESS_STEPS, JourneyState, match_departments

SYSTEM_PROMPT = (
    "你是深圳大学医院的就医陪伴助手, 服务对象是中老年人和带小孩的家长。"
    "说话要求: 句子短, 一次只说一件事, 不用专业术语, 重要的话放前面, 数字用阿拉伯数字。"
    "只回答就医相关问题; 拿不准的病情问题建议当面问医生, 不要自己下诊断。"
)

_NEXT_WORDS = ("下一步", "继续", "好了", "完成了", "搞定", "弄完了", "做完")
_BACK_WORDS = ("上一步", "回去", "返回上", "退一步")


def triage(symptoms: str) -> dict:
    """症状 -> 推荐科室。先规则匹配, 命中不足时让大模型从科室清单里选。"""
    dept_ids = match_departments(symptoms)
    used_llm = False
    if not dept_ids:
        picked = _llm_pick_department(symptoms)
        used_llm = picked is not None
        if picked:
            dept_ids = [picked]
    if not dept_ids:
        dept_ids = ["nkmz1"]
    primary = dao.get_department(dept_ids[0])
    alternatives = [d for d in (dao.get_department(i) for i in dept_ids[1:4]) if d]
    return {
        "dept": primary,
        "alternatives": alternatives,
        "exam_prep": _preps_for_dept(primary),
        "used_llm": used_llm,
        "suggestion": f"根据您说的情况, 建议先挂{primary['name']}(在{primary['floor']}楼)",
    }


def _llm_pick_department(symptoms: str):
    depts = dao.list_departments()
    lines = [f"{d['id']}:{d['name']}({d['aliases']})" for d in depts]
    prompt = (
        "患者自述症状: " + symptoms + "\n"
        "可选科室: " + "; ".join(lines) + "\n"
        "只回答最匹配的一个科室 id, 不要回答其他内容。"
    )
    try:
        answer = llm_client.chat_with_system(SYSTEM_PROMPT, prompt, max_tokens=20, temperature=0.1)
    except RuntimeError:
        return None
    answer = answer.strip().split()[0] if answer.strip() else ""
    return answer if dao.get_department(answer) else None


def _preps_for_dept(dept: dict) -> list:
    if not dept:
        return []
    exams = [e.strip().lower() for e in (dept.get("common_exams") or "").split(",") if e.strip()]
    if not exams:
        return []
    result = []
    for prep in dao.list_exam_prep():
        kws = [k.strip().lower() for k in (prep.get("keywords") or "").split(",") if k.strip()]
        kws.append(prep["exam_name"].lower())
        for exam in exams:
            if any(exam in kw or kw in exam for kw in kws):
                result.append(prep)
                break
    return result


# 检查项目 -> 导航地点(按顺序匹配, 命中即停)
EXAM_NAV = [
    ("抽血", "检验科"), ("验血", "检验科"), ("血常规", "检验科"), ("生化", "检验科"),
    ("b超", "超声科"), ("彩超", "超声科"),
    ("胃镜", "消化内镜中心"), ("肠镜", "消化内镜中心"),
    ("ct", "放射科"), ("核磁", "放射科"), ("x光", "放射科"), ("拍片", "放射科"), ("放射", "放射科"),
    ("心电", "功能检查中心"),
]


def _resolve_nav(target: str, label: str, dept, exam_names: list) -> tuple:
    """把步骤模板里的占位目标解析成(可导航的地点, 显示名)。"""
    if target == "@dept":
        name = dept["name"] if dept else ""
        return name, name
    if target == "@exam":
        joined = ",".join(exam_names).lower()
        for kw, place in EXAM_NAV:
            if kw in joined:
                return place, place
        name = dept["name"] if dept else ""
        return name, name
    return target, label


def build_process_card(dept_id: str, exams: list = None) -> dict:
    """生成结构化就诊流程卡。"""
    dept = dao.get_department(dept_id)
    exam_names = exams or ([e.strip() for e in (dept.get("common_exams") or "").split(",") if e.strip()] if dept else [])
    preps = _preps_for_dept(dept)
    steps = []
    for i, s in enumerate(PROCESS_STEPS):
        nav_target, nav_label = _resolve_nav(s["nav_target"], s["nav_label"], dept, exam_names)
        item = {
            "key": s["key"], "title": s["title"], "desc": s["desc"],
            "tips": s["tips"], "index": i,
            "nav_target": nav_target, "nav_label": nav_label,
        }
        if s["key"] == "register" and dept:
            item["poi"] = f"挂号收费处(可直达{dept['name']}, {dept['floor']}楼)"
        elif s["key"] == "exam" and exam_names:
            item["poi"] = "检查项目: " + ", ".join(exam_names)
        elif s["key"] == "medicine":
            item["poi"] = "1楼西药房取药窗口"
        steps.append(item)
    return {
        "dept": dept,
        "exam_names": exam_names,
        "exam_prep": preps,
        "steps": steps,
    }


def chat_reply(state: JourneyState, user_msg: str) -> dict:
    """对话主入口: 识别步骤推进指令, 其余交给大模型用大白话回答。"""
    command = _detect_command(user_msg)
    if command == "next":
        state.advance()
    elif command == "back":
        state.back()
    step = state.current_step()
    dept = dao.get_department(state.dept_id) if state.dept_id else None

    context = f"当前进度: 第{step['index'] + 1}步/共{step['total']}步 {step['title']} - {step['desc']}。\n"
    if dept:
        context += f"就诊科室: {dept['name']}({dept['floor']}楼)。\n"
    context += "本步提示: " + "; ".join(step["tips"])
    if command:
        context += "\n用户刚刚完成了步骤切换, 请用一句话告诉他现在要做什么。"

    try:
        reply = llm_client.chat_with_system(
            SYSTEM_PROMPT,
            context + "\n\n用户说: " + user_msg,
            max_tokens=1024,
        )
        reply = reply.replace("**", "")
    except RuntimeError:
        reply = _fallback_reply(step, dept)
    return {"reply": reply, "step": step, "state": state.to_dict()}


def _detect_command(msg: str) -> str:
    text = msg.strip()
    if any(w in text for w in _NEXT_WORDS):
        return "next"
    if any(w in text for w in _BACK_WORDS):
        return "back"
    return ""


def _fallback_reply(step: dict, dept) -> str:
    text = f"现在是第{step['index'] + 1}步: {step['title']}。{step['desc']}。"
    if dept:
        text += f"地点在{dept['name']}, {dept['floor']}楼。"
    text += "提示: " + "; ".join(step["tips"]) + "。"
    return text
