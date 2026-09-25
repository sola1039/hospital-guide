# -*- coding: utf-8 -*-
"""智能导诊接口。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao
from guide_engine import triage

router = APIRouter()


class TriageRequest(BaseModel):
    symptoms: str


@router.post("/triage")
def triage_endpoint(req: TriageRequest) -> dict:
    if not req.symptoms.strip():
        raise HTTPException(status_code=400, detail="请先描述症状")
    return triage(req.symptoms)


@router.get("/departments")
def list_departments(floor: Optional[int] = None, category: Optional[str] = None) -> list:
    return dao.list_departments(floor, category)


@router.get("/departments/{dept_id}")
def get_department(dept_id: str) -> dict:
    dept = dao.get_department(dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail=f"找不到科室: {dept_id}")
    return dept


@router.get("/exam-prep")
def exam_prep() -> list:
    return dao.list_exam_prep()


@router.get("/medicine")
def medicine() -> list:
    return dao.list_medicine_guide()
