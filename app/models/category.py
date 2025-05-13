from datetime import datetime
from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)

class CategoryCreate(CategoryBase):
    pass

class CategoryInDB(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 