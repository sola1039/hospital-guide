# -*- coding: utf-8 -*-
"""AI 对话接口: 维护会话状态, 调引导引擎生成回答。"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

import dao
from guide_engine import chat_reply
from process_kb import JourneyState

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    dept_id: Optional[str] = None


@router.post("/chat")
def chat_endpoint(req: ChatRequest) -> dict:
    message = req.message.strip()
    if not message:
        return {"reply": "您想问什么呢? 可以跟我说说哪里不舒服。", "step": None, "session_id": req.session_id}
    session_id = req.session_id or uuid4().hex[:12]
    now = datetime.now().isoformat(timespec="seconds")
    session = dao.get_session(session_id)
    if session is None:
        state = JourneyState(req.dept_id or "", [])
        dao.create_session(session_id, state.to_json(), now)
    else:
        state = JourneyState.from_json(session["state_json"])

    result = chat_reply(state, message)
    dao.update_session_state(session_id, state.to_json())
    dao.save_chat(session_id, "user", message, now)
    dao.save_chat(session_id, "assistant", result["reply"], now)
    return {"session_id": session_id, "reply": result["reply"], "step": result["step"], "state": result["state"]}


@router.get("/chat/history/{session_id}")
def chat_history(session_id: str) -> list:
    logs = dao.get_chat_logs(session_id, limit=50)
    return list(reversed(logs))
