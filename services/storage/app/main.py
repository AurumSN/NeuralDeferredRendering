import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import db as database
from .config import load_config
from .db import Experiment, Frame, ModelRecord, get_db
from .schemas import ExperimentCreate, ExperimentOut, ExperimentUpdate, FrameCreate, FrameOut, FrameUpdate, ModelCreate, ModelOut, ModelUpdate

cfg = load_config()

Path(cfg["log_file"]).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(cfg["log_file"]), logging.StreamHandler()],
)

log = logging.getLogger(cfg["service_name"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init(cfg, log)
    yield

app = FastAPI(title=cfg["service_name"], lifespan=lifespan)



@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        log.exception("%s %s -> unhandled error", request.method, request.url.path)

        return JSONResponse({"detail": "internal server error"}, status_code=500)
    
    ms = (time.perf_counter() - start) * 1000
    target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    log.info("%s %s -> %d (%.1f ms)", request.method, target, response.status_code, ms)

    return response

@app.get("/health")
def health():
    return {"service": cfg["service_name"], "status": "ok"}

def crud_router(prefix, Model, Create, Update, Out, filters):
    r = APIRouter(prefix=prefix, tags=[prefix.strip("/")])

    def get_or_404(db: Session, item_id: int):
        obj = db.get(Model, item_id)

        if obj is None:
            raise HTTPException(404, f"{Model.__name__} {item_id} not found")
        
        return obj

    def commit(db: Session):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "conflict: record already exists or violates a constraint")

    @r.post("", status_code=201, response_model=Out)
    def create(body: Create, db: Session = Depends(get_db)):
        obj = Model(**body.model_dump())
        db.add(obj)
        commit(db)
        db.refresh(obj)

        return obj

    @r.get("", summary=f"List with pagination; filters: {', '.join(filters)}")
    def list_items(request: Request, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
        q, cq = select(Model), select(func.count()).select_from(Model)

        for f in filters:
            v = request.query_params.get(f)
            if v is not None:
                q, cq = q.where(getattr(Model, f) == v), cq.where(getattr(Model, f) == v)

        items = db.scalars(q.order_by(Model.id).offset(offset).limit(limit)).all()

        return {"items": [Out.model_validate(i) for i in items], "total": db.scalar(cq), "limit": limit, "offset": offset}

    @r.get("/{item_id}", response_model=Out)
    def read(item_id: int, db: Session = Depends(get_db)):
        return get_or_404(db, item_id)

    @r.patch("/{item_id}", response_model=Out)
    def update(item_id: int, body: Update, db: Session = Depends(get_db)):
        obj = get_or_404(db, item_id)

        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)

        commit(db)
        db.refresh(obj)

        return obj

    @r.delete("/{item_id}", status_code=204)
    def delete(item_id: int, db: Session = Depends(get_db)):
        db.delete(get_or_404(db, item_id))
        commit(db)

    return r

@app.get("/models/latest", response_model=ModelOut, tags=["models"])
def latest_model(name: str, db: Session = Depends(get_db)):
    obj = db.scalars(select(ModelRecord).where(ModelRecord.name == name).order_by(ModelRecord.version.desc()).limit(1)).first()
    
    if obj is None:
        raise HTTPException(404, f"no versions of model '{name}'")
    
    return obj

app.include_router(crud_router("/frames", Frame, FrameCreate, FrameUpdate, FrameOut, ["scene", "split"]))
app.include_router(crud_router("/models", ModelRecord, ModelCreate, ModelUpdate, ModelOut, ["name", "kind"]))
app.include_router(crud_router("/experiments", Experiment, ExperimentCreate, ExperimentUpdate, ExperimentOut, ["scenario", "status"]))