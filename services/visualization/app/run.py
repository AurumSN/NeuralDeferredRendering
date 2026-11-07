import uvicorn
from .config import load_config

if __name__ == "__main__":
    cfg = load_config()
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(cfg["port"]))