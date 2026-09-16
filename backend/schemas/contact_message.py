from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ContactMessageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contact: str = Field(min_length=1, max_length=150)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("name", "contact", "message")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Este campo no puede estar vacío")
        return v


class ContactMessageResponse(BaseModel):
    id: int
    name: str
    contact: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactMessageUpdate(BaseModel):
    is_read: bool
