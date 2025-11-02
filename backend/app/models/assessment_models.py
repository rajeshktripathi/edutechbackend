from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import Base  # Fixed import

class AssessmentType(Base):
    __tablename__ = "assessment_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # e.g., "Psychology", "Career", "Skills"
    duration_minutes = Column(Integer)  # Estimated time to complete
    is_active = Column(Boolean, default=True)
    questions_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_type_id = Column(Integer, ForeignKey("assessment_types.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, likert_scale, text
    options = Column(JSON)  # For multiple choice questions
    correct_answer = Column(String(200))  # For scored questions
    points = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_type_id = Column(Integer, ForeignKey("assessment_types.id"), nullable=False)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    status = Column(String(50), default="in_progress")  # in_progress, completed, abandoned
    total_score = Column(Float)
    max_score = Column(Float)
    percentage = Column(Float)
    time_taken_seconds = Column(Integer)  # Time taken to complete in seconds

class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text)
    points_earned = Column(Float, default=0)
    response_time_seconds = Column(Integer)  # Time taken to answer this question

class VideoRecording(Base):
    __tablename__ = "video_recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    video_file_path = Column(String(500), nullable=False)
    video_duration_seconds = Column(Integer)
    file_size_bytes = Column(Integer)
    recording_started_at = Column(DateTime)
    recording_ended_at = Column(DateTime)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=func.now())

class VideoAnalysisResult(Base):
    __tablename__ = "video_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    video_recording_id = Column(Integer, ForeignKey("video_recordings.id"), nullable=False)
    
    # Emotional & Mood Analysis
    emotional_analysis = Column(JSON)
    mood_score = Column(Float)
    dominant_emotion = Column(String(100))
    
    # Intent & Purpose Analysis
    engagement_level = Column(Float)
    focus_score = Column(Float)
    confidence_level = Column(Float)
    
    # Personality & Psychological Traits
    personality_insights = Column(JSON)
    attention_metrics = Column(JSON)
    
    # Cognitive & Analytical Dimensions
    cognitive_analysis = Column(JSON)
    problem_solving_style = Column(String(100))
    
    # Overall Metrics
    overall_score = Column(Float)
    analysis_remarks = Column(Text)
    processed_at = Column(DateTime, default=func.now())

# Pydantic Models
class AssessmentTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None
    questions_count: Optional[int] = 0

class AssessmentTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    duration_minutes: Optional[int]
    is_active: bool
    questions_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    assessment_type_id: int
    question_text: str
    question_type: str
    options: Optional[List[Dict]] = None
    correct_answer: Optional[str] = None
    points: Optional[int] = 1
    order_index: Optional[int] = 0

class QuestionResponse(BaseModel):
    id: int
    assessment_type_id: int
    question_text: str
    question_type: str
    options: Optional[List[Dict]]
    points: int
    order_index: int
    
    class Config:
        from_attributes = True

class AssessmentSessionCreate(BaseModel):
    assessment_type_id: int

class AssessmentSessionResponse(BaseModel):
    id: int
    user_id: int
    assessment_type_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    total_score: Optional[float]
    max_score: Optional[float]
    percentage: Optional[float]
    time_taken_seconds: Optional[int]
    
    class Config:
        from_attributes = True

class AssessmentResponseCreate(BaseModel):
    question_id: int
    user_answer: str
    response_time_seconds: int

class VideoAnalysisRequest(BaseModel):
    process_automatically: bool = True

class VideoAnalysisResponse(BaseModel):
    id: int
    video_recording_id: int
    emotional_analysis: Optional[Dict]
    mood_score: Optional[float]
    dominant_emotion: Optional[str]
    engagement_level: Optional[float]
    focus_score: Optional[float]
    confidence_level: Optional[float]
    personality_insights: Optional[Dict]
    attention_metrics: Optional[Dict]
    cognitive_analysis: Optional[Dict]
    problem_solving_style: Optional[str]
    overall_score: Optional[float]
    analysis_remarks: Optional[str]
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CompleteAssessmentResponse(BaseModel):
    session: AssessmentSessionResponse
    video_analysis: Optional[VideoAnalysisResponse] = None
    assessment_type: AssessmentTypeResponse