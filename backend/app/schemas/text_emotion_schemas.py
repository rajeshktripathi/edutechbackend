# backend/schemas/text_emotion_schemas.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, date

# Request Schemas
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")
    user_id: str = Field(..., description="User identifier")
    language: str = Field("en", description="Language of the text")
    session_id: Optional[str] = Field(None, description="Session identifier")

class BatchTextAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, description="List of texts to analyze")
    user_id: str = Field(..., description="User identifier")
    language: str = Field("en", description="Language of the texts")
    session_id: Optional[str] = Field(None, description="Session identifier")

# Response Schemas
class EmotionAnalysisResponse(BaseModel):
    id: Optional[int] = Field(None, description="Analysis result ID")
    emotions: Dict[str, float] = Field(..., description="Emotion probabilities")
    dominant_emotion: str = Field(..., description="Dominant emotion detected")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    analysis_type: str = Field("text", description="Type of analysis")
    timestamp: str = Field(..., description="Analysis timestamp")
    user_id: str = Field(..., description="User identifier")
    metadata: Dict[str, Any] = Field(..., description="Analysis metadata")
    text_preview: Optional[str] = Field(None, description="Text preview")
    session_id: Optional[str] = Field(None, description="Session identifier")

class TextEmotionResultResponse(BaseModel):
    id: int = Field(..., description="Result ID")
    user_id: str = Field(..., description="User identifier")
    text_preview: str = Field(..., description="Text content preview")
    emotions: Dict[str, float] = Field(..., description="Emotion probabilities")
    dominant_emotion: str = Field(..., description="Dominant emotion")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    analysis_type: str = Field(..., description="Analysis type")
    timestamp: str = Field(..., description="Analysis timestamp")
    analysis_date: str = Field(..., description="Analysis date")
    text_length: int = Field(..., ge=0, description="Text length in characters")
    word_count: int = Field(..., ge=0, description="Word count")
    language: str = Field(..., description="Text language")
    session_id: Optional[str] = Field(None, description="Session identifier")

class SessionSummary(BaseModel):
    session_date: str = Field(..., description="Session date")
    session_id: Optional[str] = Field(None, description="Session identifier")
    total_analyses: int = Field(..., ge=0, description="Total analyses in session")
    emotion_distribution: Dict[str, int] = Field(..., description="Emotion frequency distribution")
    average_confidence: float = Field(..., ge=0, le=1, description="Average confidence score")
    dominant_emotions: List[Dict[str, Any]] = Field(..., description="Top emotions by confidence")
    text_statistics: Dict[str, Any] = Field(..., description="Text analysis statistics")

class DateSessionResponse(BaseModel):
    sessions: List[SessionSummary] = Field(..., description="List of sessions")
    total_sessions: int = Field(..., ge=0, description="Total number of sessions")
    total_analyses: int = Field(..., ge=0, description="Total number of analyses")

class SessionDetailsResponse(BaseModel):
    session_date: str = Field(..., description="Session date")
    session_id: Optional[str] = Field(None, description="Session identifier")
    analyses: List[TextEmotionResultResponse] = Field(..., description="Session analyses")
    summary: SessionSummary = Field(..., description="Session summary")

class PaginatedResults(BaseModel):
    results: List[TextEmotionResultResponse] = Field(..., description="Paginated results")
    total_count: int = Field(..., ge=0, description="Total number of results")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

class SummaryReport(BaseModel):
    user_id: str = Field(..., description="User identifier")
    period: str = Field(..., description="Report period")
    total_analyses: int = Field(..., ge=0, description="Total analyses in period")
    emotion_distribution: Dict[str, int] = Field(..., description="Emotion distribution")
    average_confidence: float = Field(..., ge=0, le=1, description="Average confidence")
    most_common_emotion: str = Field(..., description="Most common emotion")
    text_statistics: Dict[str, Any] = Field(..., description="Text statistics")
    timeframe: Dict[str, str] = Field(..., description="Timeframe of the report")

class ExportResponse(BaseModel):
    filename: str = Field(..., description="Export filename")
    content: Any = Field(..., description="Export content")
    format: str = Field(..., description="Export format")

class ModelStatusResponse(BaseModel):
    model_loaded: bool = Field(..., description="Model loading status")
    supported_emotions: List[str] = Field(..., description="Supported emotions")
    supported_languages: List[str] = Field(..., description="Supported languages")
    analysis_methods: List[str] = Field(..., description="Analysis methods")
    status: str = Field(..., description="Service status")
    database_connected: bool = Field(..., description="Database connection status")