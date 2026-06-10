from fastapi.responses import StreamingResponse
from pdf_generator import generate_pdf_report
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
from models import Server, Scan, Finding
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Security Validation Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Security Validation Platform API is running"}

@app.post("/api/scan")
def receive_scan(payload: schemas.ScanRequest, db: Session = Depends(get_db)):
    server = db.query(Server).filter(
        Server.hostname == payload.hostname
    ).first()

    if not server:
        server = Server(
            hostname=payload.hostname,
            ip_address=payload.ip_address
        )
        db.add(server)
        db.commit()
        db.refresh(server)

    scan = Scan(server_id=server.id, score=payload.score)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    for f in payload.findings:
        finding = Finding(
            scan_id=scan.id,
            control_id=f.control_id,
            title=f.title,
            severity=f.severity,
            passed=f.passed,
            detail=f.detail
        )
        db.add(finding)

    db.commit()

    return {
        "message": "Scan received successfully",
        "server": payload.hostname,
        "score": payload.score,
        "scan_id": scan.id
    }

@app.get("/api/servers", response_model=List[schemas.ServerOut])
def get_servers(db: Session = Depends(get_db)):
    return db.query(Server).all()

@app.get("/api/report/{server_id}", response_model=schemas.ReportOut)
def get_report(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    latest_scan = db.query(Scan).filter(
        Scan.server_id == server_id
    ).order_by(Scan.scanned_at.desc()).first()

    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans found for this server")

    return {"server": server, "latest_scan": latest_scan}
    
@app.get("/api/report/{server_id}/pdf")
def download_pdf_report(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    latest_scan = db.query(Scan).filter(
        Scan.server_id == server_id
    ).order_by(Scan.scanned_at.desc()).first()

    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans found")

    pdf_buffer = generate_pdf_report(server, latest_scan)

    filename = f"security-report-{server.hostname}-{latest_scan.scanned_at.strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )