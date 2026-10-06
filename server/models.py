from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    session_id: Optional[str] = None
    case_type: Optional[str] = None  # None = let triage decide (was wrongly defaulted to "arrest_rights")
    slots: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    chunk_id: str
    ref: str
    quote: str


class AnswerSection(BaseModel):
    heading: str
    content: str
    citations: List[Citation] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    status: Literal["answered", "needs_info", "emergency", "abstained"]
    case_type: str = "general_statute"
    sections: List[AnswerSection] = Field(default_factory=list)
    computed_timelines: Dict[str, Any] = Field(default_factory=dict)
    missing_slots: List[str] = Field(default_factory=list)
    rights: List[str] = Field(default_factory=list)
    helplines: List[Dict[str, str]] = Field(default_factory=list)
    disclaimer: str
