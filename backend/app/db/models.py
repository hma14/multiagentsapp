from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class PromptResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: str
    results: str
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
