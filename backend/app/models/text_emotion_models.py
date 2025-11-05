# backend/models/text_emotion_models.py
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, Date, func
from app.database.database import Base

class TextEmotionResult(Base):
    __tablename__ = "text_emotion_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    text_content = Column(Text, nullable=False)
    emotions = Column(Text, nullable=False)  # JSON string of emotions
    dominant_emotion = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    analysis_type = Column(String, default="text")
    timestamp = Column(DateTime, default=func.now())
    analysis_date = Column(Date, default=func.current_date())
    text_length = Column(Integer)
    word_count = Column(Integer)
    language = Column(String, default="en")
    session_id = Column(String, index=True)