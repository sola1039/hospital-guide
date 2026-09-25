# -*- coding: utf-8 -*-
"""挂号演示接口: 本地假数据流程, 不接真实支付。"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import dao

router = APIRouter()


class RegisterRequest(BaseModel):
    patient_name: str
    doctor_id: str
    visit_date: str
    slot: str


@router.get("/demo/doctors")
def list_doctors(dept_id: Optional[str] = None) -> list:
    return dao.list_doctors(dept_id)


@router.post("/demo/register")
def register(req: RegisterRequest) -> dict:
    doctor = dao.get_doctor(req.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail=f"找不到医生: {req.doctor_id}")
    if not req.patient_name.strip():
        raise HTTPException(status_code=400, detail="请填写就诊人姓名")
    if not req.visit_date.strip() or not req.slot.strip():
        raise HTTPException(status_code=400, detail="请选择就诊日期和时段")
    reg_id = "R" + datetime.now().strftime("%Y%m%d") + uuid4().hex[:6]
    now = datetime.now().isoformat(timespec="seconds")
    dao.create_registration(reg_id, req.patient_name.strip(), doctor["id"], doctor["dept_id"],
                            req.visit_date.strip(), req.slot.strip(), now)
    dept = dao.get_department(doctor["dept_id"])
    return {
        "registration_id": reg_id,
        "patient_name": req.patient_name.strip(),
        "doctor": doctor["name"],
        "dept": dept["name"] if dept else doctor["dept_id"],
        "visit_date": req.visit_date,
        "slot": req.slot,
        "status": "已预约(演示)",
    }


@router.get("/demo/registrations")
def registrations(patient_name: Optional[str] = None) -> list:
    rows = dao.list_registrations(patient_name)
    result = []
    for r in rows:
        doctor = dao.get_doctor(r["doctor_id"])
        dept = dao.get_department(r["dept_id"])
        item = dict(r)
        item["doctor_name"] = doctor["name"] if doctor else r["doctor_id"]
        item["dept_name"] = dept["name"] if dept else r["dept_id"]
        item["floor"] = dept["floor"] if dept else None
        result.append(item)
    return result
