from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="server")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    score = Column(Float)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("Server", back_populates="scans")
    findings = relationship("Finding", back_populates="scan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    control_id = Column(String)
    title = Column(String)
    severity = Column(String)
    passed = Column(Boolean)
    detail = Column(Text)

    scan = relationship("Scan", back_populates="findings")