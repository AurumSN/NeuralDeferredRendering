from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

Split = Literal["train", "val", "test"]

class FrameCreate(BaseModel):
    scene: str
    split: Split = "train"
    camera: dict = {}
    light: dict = {}
    gbuffer_path: str
    target_path: str

class FrameUpdate(BaseModel):
    scene: str | None = None
    split: Split | None = None
    camera: dict | None = None
    light: dict | None = None
    gbuffer_path: str | None = None
    target_path: str | None = None

class FrameOut(FrameCreate, _Out):
    pass

class ModelCreate(BaseModel):
    name: str
    version: int = Field(ge=1)
    kind: str
    metrics: dict = {}
    weights_path: str | None = None

class ModelUpdate(BaseModel):
    kind: str | None = None
    metrics: dict | None = None
    weights_path: str | None = None

class ModelOut(ModelCreate, _Out):
    pass

Status = Literal["pending", "running", "done", "failed"]

class ExperimentCreate(BaseModel):
    scenario: str
    params: dict = {}
    status: Status = "pending"
    result: dict = {}

class ExperimentUpdate(BaseModel):
    status: Status | None = None
    result: dict | None = None

class ExperimentOut(ExperimentCreate, _Out):
    pass
