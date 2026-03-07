from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator
import uuid


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(None, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    expires_at: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)

    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) < 3:
            raise ValueError('Custom alias must be at least 3 characters long')
        return v


class LinkResponse(BaseModel):
    id: uuid.UUID
    short_code: str
    original_url: str
    short_url: str
    custom_alias: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    
    class Config:
        from_attributes = True


class LinkStats(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    last_used_at: Optional[datetime] = None
    category: Optional[str] = None
    
    class Config:
        from_attributes = True


class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)


class LinkSearch(BaseModel):
    original_url: HttpUrl
