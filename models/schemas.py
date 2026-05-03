from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UserRecord(BaseModel):
    user_id: int
    username: str | None
    first_seen: datetime
    last_activity: datetime
    total_tzs: int = 0


class TZSpec(BaseModel):
    id: int | None = None
    user_id: int
    content: str
    created_at: datetime | None = None


class GenerationLog(BaseModel):
    user_id: int
    type: Literal["tz", "image", "video", "code_audit"]
    model_used: str
    success: bool
    tokens_used: int | None = None
