import os
from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

url = (
    os.getenv("DATABASE_URL", "sqlite:///./ecocycle.db")
    .replace("postgres://", "postgresql+psycopg://")
    .replace("postgresql://", "postgresql+psycopg://")
)
engine = create_engine(url, pool_pre_ping=True)
if url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def foreign_keys(conn, _record):
        conn.execute("PRAGMA foreign_keys=ON")


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def database() -> Iterator[Session]:
    with Session(engine) as db:
        yield db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), default="citizen")
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class LoginSession(Base):
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires: Mapped[datetime] = mapped_column(DateTime)


class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    predictions: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(Text, default="")
    material: Mapped[str | None] = mapped_column(String(16))
    weight: Mapped[float | None] = mapped_column(Float)
    breakdown: Mapped[str | None] = mapped_column(Text)
    ward: Mapped[str] = mapped_column(String(80), default="Central")


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), unique=True)
    material: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(String(400), default="")
    status: Mapped[str] = mapped_column(String(16), default="pending")


class Center(Base):
    __tablename__ = "centers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    materials: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(200))


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(240))
    created: Mapped[datetime] = mapped_column(DateTime, default=now)
