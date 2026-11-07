import logging
from pathlib import Path
from fastapi import FastAPI
from .config import load_config

cfg = load_config()

Path(cfg["log_file"]).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(cfg["log_file"]), logging.StreamHandler()],
)

log = logging.getLogger(cfg["service_name"])

app = FastAPI(title=cfg["service_name"])



@app.get("/health")
def health():
    return {"service": cfg["service_name"], "status": "ok"}


from fastapi import HTTPException

_files = None
_cursor = 0

def _list_files():
    global _files

    if _files is None:
        d = Path(cfg["dataset_dir"])

        if not d.is_dir():
            raise HTTPException(503, f"dataset_dir not found: {d}")
        
        _files = sorted(p.name for p in d.iterdir() if p.is_file())

    return _files


@app.get("/batch")
def get_batch(size: int | None = None):
    global _cursor

    files = _list_files()
    size = size or cfg["batch_size"]

    if size <= 0:
        raise HTTPException(400, "size must be positive")
    
    if _cursor >= len(files):
        raise HTTPException(410, "dataset exhausted, call POST /reset")
    
    batch = files[_cursor:_cursor + size]
    log.info("batch cursor=%d size=%d returned=%d", _cursor, size, len(batch))
    _cursor += len(batch)

    return {"items": batch, "next_cursor": _cursor, "total": len(files)}


@app.post("/reset")
def reset():
    global _cursor, _files

    _cursor, _files = 0, None

    log.info("cursor reset")

    return {"status": "reset"}
