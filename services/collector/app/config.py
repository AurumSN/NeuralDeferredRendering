import os
from pathlib import Path
import yaml

def load_config() -> dict:
    path = Path(os.getenv("CONFIG_PATH", "/app/config.yaml"))

    if not path.exists():
        raise RuntimeError(f"Config file not found: {path}")
    
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}