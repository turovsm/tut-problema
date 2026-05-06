from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: Optional[T] = None
    message: Optional[str] = None

class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=2)

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        lng, lat = v
        if not (-180 <= lng <= 180): raise ValueError(f"Longitude error: {lng}")
        if not (-90 <= lat <= 90): raise ValueError(f"Latitude error: {lat}")
        return v