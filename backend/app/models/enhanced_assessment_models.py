# app/models/enhanced_assessment_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class EnhancedAssessmentType(Base):
    __tablename__ = "enhanced_assessment_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=30)
    questions_count = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("EnhancedQuestion", back_populates="assessment_type")
    sessions = relationship("EnhancedAssessmentSession", back_populates="assessment_type")

class EnhancedQuestion(Base):
    __tablename__ = "enhanced_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_type_id = Column(Integer, ForeignKey("enhanced_assessment_types.id"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")
    options = Column(JSON)
    correct_answer = Column(String(500))
    points = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    assessment_type = relationship("EnhancedAssessmentType", back_populates="questions")
    responses = relationship("EnhancedAssessmentResponse", back_populates="question")

class EnhancedAssessmentSession(Base):
    __tablename__ = "enhanced_assessment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    assessment_type_id = Column(Integer, ForeignKey("enhanced_assessment_types.id"))
    session_code = Column(String(50), default=lambda: str(uuid.uuid4())[:8])
    status = Column(String(20), default="in_progress")
    total_score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    percentage = Column(Float, default=0)
    time_taken_seconds = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    assessment_type = relationship("EnhancedAssessmentType", back_populates="sessions")
    responses = relationship("EnhancedAssessmentResponse", back_populates="session")
    video_recordings = relationship("EnhancedVideoRecording", back_populates="session")
    mock_results = relationship("MockVideoAnalysis", back_populates="session")

class EnhancedAssessmentResponse(Base):
    __tablename__ = "enhanced_assessment_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("enhanced_assessment_sessions.id"))
    question_id = Column(Integer, ForeignKey("enhanced_questions.id"))
    user_answer = Column(String(1000))
    is_correct = Column(Boolean, default=False)
    points_earned = Column(Float, default=0)
    response_time_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("EnhancedAssessmentSession", back_populates="responses")
    question = relationship("EnhancedQuestion", back_populates="responses")

class EnhancedVideoRecording(Base):
    __tablename__ = "enhanced_video_recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("enhanced_assessment_sessions.id"))
    video_file_path = Column(String(500))
    video_duration_seconds = Column(Integer)
    file_size_bytes = Column(Integer)
    recording_started_at = Column(DateTime)
    recording_ended_at = Column(DateTime)
    processing_status = Column(String(20), default="pending")
    download_path = Column(String(500))
    last_downloaded_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("EnhancedAssessmentSession", back_populates="video_recordings")
    mock_analysis = relationship("MockVideoAnalysis", back_populates="video_recording")

class MockVideoAnalysis(Base):
    __tablename__ = "mock_video_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("enhanced_assessment_sessions.id"))
    video_recording_id = Column(Integer, ForeignKey("enhanced_video_recordings.id"))
    
    # Analysis fields
    emotional_analysis = Column(JSON)
    mood_score = Column(Float)
    dominant_emotion = Column(String(50))
    engagement_level = Column(Float)
    focus_score = Column(Float)
    confidence_level = Column(Float)
    motivation_level = Column(Float)
    personality_insights = Column(JSON)
    attention_metrics = Column(JSON)
    cognitive_analysis = Column(JSON)
    problem_solving_style = Column(String(50))
    career_predictions = Column(JSON)
    overall_score = Column(Float)
    analysis_remarks = Column(Text)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("EnhancedAssessmentSession", back_populates="mock_results")
    video_recording = relationship("EnhancedVideoRecording", back_populates="mock_analysis")