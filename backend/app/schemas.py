from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None
    created_at: datetime


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bin_id: str
    method: str
    path: str
    headers: dict
    query: dict
    body: str
    content_type: str | None
    source_ip: str | None
    truncated: bool
    received_at: datetime
