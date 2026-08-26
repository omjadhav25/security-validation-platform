import os
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import schemas
from auth import (
    authenticate_user,
    create_access_token,
    generate_api_key,
    get_current_user,
    get_user_from_api_key,
    hash_password,
)
from database import Base, engine, get_db
from models import Finding, Scan, Server, User
from pdf_generator import generate_pdf_report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Security Validation Platform", version="2.0.0")

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://security-validation-platform.vercel.app")
# Public base URL of THIS backend, used to build the copy-paste install commands.
BACKEND_URL = os.getenv("BACKEND_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
def root():
    return {"message": "Security Validation Platform API is running"}


# --- Auth -----------------------------------------------------------------
@app.post("/api/auth/register", response_model=schemas.TokenResponse)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail="That username is already taken")

    user = User(
        username=username,
        hashed_password=hash_password(payload.password),
        api_key=generate_api_key(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.username)
    return {"access_token": token, "api_key": user.api_key}


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username.strip().lower(), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(subject=user.username)
    return {"access_token": token, "api_key": user.api_key}


@app.get("/api/me", response_model=schemas.MeOut)
def me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "api_key": current_user.api_key,
        "install_linux": (
            f'curl -fsSL {BACKEND_URL}/public/agent-linux.sh | '
            f'bash -s -- {current_user.api_key}'
        ),
        "install_windows": (
            f'$env:SVP_API_KEY="{current_user.api_key}"; '
            f'irm {BACKEND_URL}/public/agent-windows.ps1 | iex'
        ),
    }


@app.post("/api/auth/regenerate-key", response_model=schemas.MeOut)
def regenerate_key(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.api_key = generate_api_key()
    db.commit()
    db.refresh(current_user)
    return me(current_user)


# --- Scanning (called by the install scripts, authenticated via API key) --
@app.post("/api/scan")
def receive_scan(
    payload: schemas.ScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_api_key),
):
    server = (
        db.query(Server)
        .filter(Server.user_id == current_user.id, Server.hostname == payload.hostname)
        .first()
    )

    if not server:
        server = Server(
            user_id=current_user.id,
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            os_type=payload.os_type or "linux",
        )
        db.add(server)
        db.commit()
        db.refresh(server)
    else:
        server.ip_address = payload.ip_address
        db.commit()

    scan = Scan(server_id=server.id, score=payload.score)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    for f in payload.findings:
        db.add(Finding(
            scan_id=scan.id,
            control_id=f.control_id,
            title=f.title,
            severity=f.severity,
            passed=f.passed,
            detail=f.detail,
        ))
    db.commit()

    return {
        "message": "Scan received successfully",
        "server": payload.hostname,
        "score": payload.score,
        "scan_id": scan.id,
    }


# --- Dashboard (JWT-protected, always scoped to the logged-in user) --------
def _server_out(db: Session, server: Server) -> dict:
    latest = (
        db.query(Scan)
        .filter(Scan.server_id == server.id)
        .order_by(Scan.scanned_at.desc())
        .first()
    )
    return {
        "id": server.id,
        "hostname": server.hostname,
        "ip_address": server.ip_address,
        "os_type": server.os_type,
        "created_at": server.created_at,
        "latest_score": latest.score if latest else None,
        "latest_scanned_at": latest.scanned_at if latest else None,
    }


@app.get("/api/servers", response_model=List[schemas.ServerOut])
def get_servers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    servers = db.query(Server).filter(Server.user_id == current_user.id).all()
    return [_server_out(db, s) for s in servers]


def _get_owned_server_or_404(db: Session, server_id: int, current_user: User) -> Server:
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.user_id == current_user.id)
        .first()
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@app.get("/api/report/{server_id}", response_model=schemas.ReportOut)
def get_report(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = _get_owned_server_or_404(db, server_id, current_user)

    latest_scan = (
        db.query(Scan)
        .filter(Scan.server_id == server_id)
        .order_by(Scan.scanned_at.desc())
        .first()
    )
    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans found for this server")

    return {"server": _server_out(db, server), "latest_scan": latest_scan}


@app.get("/api/report/{server_id}/pdf")
def download_pdf_report(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = _get_owned_server_or_404(db, server_id, current_user)

    latest_scan = (
        db.query(Scan)
        .filter(Scan.server_id == server_id)
        .order_by(Scan.scanned_at.desc())
        .first()
    )
    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans found")

    pdf_buffer = generate_pdf_report(server, latest_scan)
    filename = f"security-report-{server.hostname}-{latest_scan.scanned_at.strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
