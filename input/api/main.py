# -*- coding: utf-8 -*-
"""FastAPI 服务入口。

启动: cd 其余项目/医院辅助 && pip install -r input/api/requirements.txt && uvicorn input.api.main:app --reload
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "input", "database"))
sys.path.insert(0, os.path.join(BASE, "asset", "navigation"))
sys.path.insert(0, os.path.join(BASE, "asset", "ai_core"))
sys.path.insert(0, os.path.join(BASE, "input", "api"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import chat as chat_routes
import demo as demo_routes
import guide as guide_routes
import journey as journey_routes
import navigate as navigate_routes

app = FastAPI(title="医院就医辅助服务", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guide_routes.router, prefix="/api", tags=["导诊"])
app.include_router(journey_routes.router, prefix="/api", tags=["就诊流程"])
app.include_router(navigate_routes.router, prefix="/api", tags=["院内导航"])
app.include_router(chat_routes.router, prefix="/api", tags=["AI对话"])
app.include_router(demo_routes.router, prefix="/api", tags=["挂号演示"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
