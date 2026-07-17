from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class IdeaRequest(BaseModel):
    idea: str = Field(..., min_length=50, max_length=5000)
    session_id: Optional[str] = Field(None, max_length=64)


class AnalysisResponse(BaseModel):
    idea_id: int
    analysis: str
    sections: list[str]


class ReviewRequest(BaseModel):
    idea_id: int
    text: str = Field(..., min_length=10, max_length=1000)
    rating: int = Field(..., ge=1, le=5)


class ReviewResponse(BaseModel):
    id: int
    idea_id: int
    text: str
    rating: int
    created_at: str


class WaitlistRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    session_id: Optional[str] = Field(None, max_length=64)


class TrackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    event_type: Literal["visit", "cta_click"]
    meta: Optional[dict] = None
