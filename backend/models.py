from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Personal key embedded in the copy-paste install command. Long-lived,
    # not a password - can be regenerated any time without changing login.
    api_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    servers = relationship("Server", back_populates="owner", cascade="all, delete-orphan")


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    hostname = Column(String, index=True)
    ip_address = Column(String)
    os_type = Column(String, default="linux")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="servers")
    scans = relationship("Scan", back_populates="server", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False, index=True)
    score = Column(Float)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    server = relationship("Server", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    control_id = Column(String)
    title = Column(String)
    severity = Column(String)
    passed = Column(Boolean)
    detail = Column(Text)

    scan = relationship("Scan", back_populates="findings")
