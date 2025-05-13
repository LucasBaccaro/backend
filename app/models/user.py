from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, computed_field, model_validator

class UserRole(str, Enum):
    CLIENT = "client"
    WORKER = "worker"

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    dni: str = Field(..., min_length=7, max_length=8)
    phone_number: str = Field(..., min_length=10, max_length=15)
    role: Optional[UserRole] = None  # Made optional
    location_id: Optional[str] = None

class ClientBase(UserBase):
    address: str = Field(..., min_length=5, max_length=200)  # Dirección requerida para clientes

class WorkerBase(UserBase):
    address: Optional[str] = None  # Dirección opcional para workers
    category_id: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @model_validator(mode='after')
    def validate_role_specific_fields(self):
        if self.role == UserRole.CLIENT:
            if not hasattr(self, 'address') or not self.address:
                raise ValueError("Address is required for clients")
            if not self.location_id:
                raise ValueError("Location is required for clients")
        return self

class ClientCreate(ClientBase, UserCreate):
    def __init__(self, **data):
        super().__init__(**data)
        self.role = UserRole.CLIENT  # Set role automatically

class WorkerCreate(WorkerBase, UserCreate):
    location_id: str  # Para workers, location_id es requerido

    def __init__(self, **data):
        super().__init__(**data)
        self.role = UserRole.WORKER  # Set role automatically

class UserInDB(UserBase):
    id: str
    is_active: bool = True
    is_verified: Optional[bool] = None  # None for clients, True/False for workers
    category_id: Optional[str] = None
    address: Optional[str] = None
    average_rating: float = 0
    ratings_count: int = 0

    @computed_field
    def needs_verification(self) -> bool:
        """Returns True if the user is a worker and needs verification"""
        return self.role == UserRole.WORKER and not self.is_verified

class UserResponse(UserInDB):
    class Config:
        from_attributes = True 