# -*- coding: utf-8 -*-
"""就诊流程卡与步骤推进接口。步骤推进走状态机, 不经过大模型。"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
from guide_engine import build_process_card
from process_kb import JourneyState

router = APIRouter()


class CardRequest(BaseModel):
    dept_id: str
    exams: Optional[list] = None


class SessionRequest(BaseModel):
    session_id: Optional[str] = None
    dept_id: str
    exams: Optional[list] = None


class StepRequest(BaseModel):
    session_id: str
    action: str  # next / back / jump
    key: Optional[str] = None


@router.post("/journey/card")
def journey_card(req: CardRequest) -> dict:
    if dao.get_department(req.dept_id) is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {req.dept_id}")
    return build_process_card(req.dept_id, req.exams)


@router.post("/journey/session")
def create_session(req: SessionRequest) -> dict:
    if dao.get_department(req.dept_id) is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {req.dept_id}")
    session_id = req.session_id or uuid4().hex[:12]
    state = JourneyState(req.dept_id, req.exams or [])
    now = datetime.now().isoformat(timespec="seconds")
    if dao.get_session(session_id):
        dao.update_session_state(session_id, state.to_json())
    else:
        dao.create_session(session_id, state.to_json(), now)
    return {"session_id": session_id, "step": state.current_step(), "card": build_process_card(req.dept_id, req.exams)}


@router.post("/journey/step")
def step_action(req: StepRequest) -> dict:
    session = dao.get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在, 请先创建")
    state = JourneyState.from_json(session["state_json"])
    if req.action == "next":
        step = state.advance()
    elif req.action == "back":
        step = state.back()
    elif req.action == "jump" and req.key:
        step = state.jump_to(req.key)
    else:
        raise HTTPException(status_code=400, detail="action 需为 next / back / jump")
    dao.update_session_state(req.session_id, state.to_json())
    return {"step": step, "state": state.to_dict()}


@router.get("/journey/session/{session_id}")
def get_session_state(session_id: str) -> dict:
    session = dao.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    state = JourneyState.from_json(session["state_json"])
    return {"session_id": session_id, "step": state.current_step(), "state": state.to_dict()}
