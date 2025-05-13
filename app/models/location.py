from datetime import datetime
from pydantic import BaseModel, Field

class LocationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class LocationCreate(LocationBase):
    pass

class LocationInDB(LocationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 