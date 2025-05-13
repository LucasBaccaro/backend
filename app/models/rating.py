from pydantic import BaseModel, Field

class ServiceRatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5) 