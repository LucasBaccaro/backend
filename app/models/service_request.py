from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ServiceRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"

class ServiceRequestBase(BaseModel):
    worker_id: str = Field(..., description="ID del trabajador")
    description: str = Field(..., min_length=5, max_length=500)

class ServiceRequestCreate(ServiceRequestBase):
    pass

class ServiceRequestInDB(ServiceRequestBase):
    id: str
    client_id: str
    status: ServiceRequestStatus
    created_at: datetime
    updated_at: datetime

class ServiceRequestResponse(ServiceRequestInDB):
    class Config:
        from_attributes = True 