from pydantic import BaseModel
from typing import List
from datetime import datetime


class FindingSchema(BaseModel):
    control_id: str
    title: str
    severity: str
    passed: bool
    detail: str

    model_config = {"from_attributes": True}


class ScanRequest(BaseModel):
    hostname: str
    ip_address: str
    score: float
    findings: List[FindingSchema]


class FindingOut(BaseModel):
    control_id: str
    title: str
    severity: str
    passed: bool
    detail: str

    model_config = {"from_attributes": True}


class ScanOut(BaseModel):
    id: int
    score: float
    scanned_at: datetime
    findings: List[FindingOut]

    model_config = {"from_attributes": True}


class ServerOut(BaseModel):
    id: int
    hostname: str
    ip_address: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    server: ServerOut
    latest_scan: ScanOut

    model_config = {"from_attributes": True}