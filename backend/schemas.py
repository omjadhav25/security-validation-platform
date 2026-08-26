from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --- Auth -------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str


class MeOut(BaseModel):
    username: str
    api_key: str
    install_linux: str
    install_windows: str


# --- Scanning -----------------------------------------------------------
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
    os_type: Optional[str] = "linux"
    score: float
    findings: List[FindingSchema]


class FindingOut(FindingSchema):
    pass


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
    os_type: str
    created_at: datetime
    latest_score: Optional[float] = None
    latest_scanned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    server: ServerOut
    latest_scan: ScanOut

    model_config = {"from_attributes": True}
