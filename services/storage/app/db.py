import os
import time
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = None
SessionLocal = None

def _now() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Frame(Base):
    __tablename__ = "frames"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene: Mapped[str] = mapped_column(String, index=True)
    split: Mapped[str] = mapped_column(String, index=True, default="train")
    camera: Mapped[dict] = mapped_column(JSON, default=dict)
    light: Mapped[dict] = mapped_column(JSON, default=dict)
    gbuffer_path: Mapped[str] = mapped_column(String)
    target_path: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

class ModelRecord(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_name_version"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String, index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    weights_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario: Mapped[str] = mapped_column(String, index=True)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, index=True, default="pending")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

def build_url(cfg: dict):
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    
    d = cfg["db"]

    return URL.create(
        "postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=d["host"], port=d["port"],
        database=os.environ["POSTGRES_DB"],
    )

def init(cfg: dict, log) -> None:
    global engine, SessionLocal

    engine = create_engine(build_url(cfg), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    retries = cfg["db"].get("connect_retries", 30)
    delay = cfg["db"].get("retry_delay_sec", 1)

    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            log.info("database ready")

            return
        except Exception as e:
            log.warning("database not ready (%d/%d): %s", attempt, retries, type(e).__name__)
            time.sleep(delay)

    raise RuntimeError("database is unavailable")

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def ping() -> bool:
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))

        return True
    except Exception:
        return False