from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IdeaRequest(BaseModel):
    idea: str = Field(..., min_length=50, max_length=5000)


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
