from typing import TypeVar, Generic, Optional, List
from pydantic import BaseModel

T = TypeVar('T')

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[str]] = None

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None 