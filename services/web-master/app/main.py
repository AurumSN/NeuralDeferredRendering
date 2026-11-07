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

import httpx

@app.get("/status")
def status():
    result = {}

    for name, url in cfg["services"].items():
        try:
            r = httpx.get(f"{url}/health", timeout=2.0)
            result[name] = "ok" if r.status_code == 200 else f"http {r.status_code}"
        except httpx.HTTPError as e:
            result[name] = f"unreachable: {type(e).__name__}"

    return result