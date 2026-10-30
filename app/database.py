from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from app.config import DATABASE_URL

class Base(DeclarativeBase): pass
class Alert(Base):
    __tablename__="alerts"
    id: Mapped[str]=mapped_column(String, primary_key=True); created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda:datetime.now(timezone.utc))
    status: Mapped[str]=mapped_column(String, default="open"); predicted_class: Mapped[str]=mapped_column(String); attack_probability: Mapped[float]=mapped_column(Float); anomaly_score: Mapped[float]=mapped_column(Float); risk_score: Mapped[float]=mapped_column(Float); severity: Mapped[str]=mapped_column(String); flow: Mapped[dict]=mapped_column(JSON); evidence: Mapped[dict]=mapped_column(JSON, default=dict)
    investigations: Mapped[list["Investigation"]]=relationship(back_populates="alert")
class Investigation(Base):
    __tablename__="investigations"
    id: Mapped[str]=mapped_column(String, primary_key=True); alert_id: Mapped[str]=mapped_column(ForeignKey("alerts.id")); created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda:datetime.now(timezone.utc)); summary: Mapped[str]=mapped_column(Text); recommendation: Mapped[str]=mapped_column(Text); sources: Mapped[list]=mapped_column(JSON); trace: Mapped[list]=mapped_column(JSON)
    alert: Mapped[Alert]=relationship(back_populates="investigations")
class Decision(Base):
    __tablename__="analyst_decisions"
    id: Mapped[str]=mapped_column(String, primary_key=True); investigation_id: Mapped[str]=mapped_column(ForeignKey("investigations.id")); decision: Mapped[str]=mapped_column(String); comment: Mapped[str]=mapped_column(Text, default=""); created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda:datetime.now(timezone.utc))

engine=create_engine(DATABASE_URL, connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {})
def init_db(): Base.metadata.create_all(engine)
def session(): return Session(engine)
def recent_alerts(limit: int=100):
    with session() as s: return list(s.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(limit)))
