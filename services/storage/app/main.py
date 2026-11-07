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

log.info("Hello, World!")

app = FastAPI(title=cfg["service_name"])



@app.get("/health")
def health():
    return {"service": cfg["service_name"], "status": "ok"}
