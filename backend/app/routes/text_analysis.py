# backend/app/api/endpoints/text_analysis.py
import re
import json
import numpy as np
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

# Hugging Face imports
from transformers import pipeline
import torch

from app.database import get_db
from app.models.text_emotion_models import TextEmotionResult
from app.schemas.text_emotion_schemas import (
    TextAnalysisRequest,
    BatchTextAnalysisRequest,
    EmotionAnalysisResponse,
    TextEmotionResultResponse,
    DateSessionResponse,
    SessionDetailsResponse,
    PaginatedResults,
    SummaryReport,
    ExportResponse,
    ModelStatusResponse,
    SessionSummary
)

router = APIRouter(prefix="/api/text", tags=["text-assessments"])

class HuggingFaceEmotionAnalyzer:
    def __init__(self):
        self.model_name = "j-hartmann/emotion-english-distilroberta-base"
        self.supported_emotions = ['anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise']
        self.emotion_mapping = {
            'anger': 'angry',
            'disgust': 'disgusted', 
            'fear': 'fearful',
            'joy': 'happy',
            'neutral': 'neutral',
            'sadness': 'sad',
            'surprise': 'surprised'
        }
        
        self.model_loaded = False
        self.classifier = None
        self.load_model()
    
    def load_model(self):
        """Load the Hugging Face emotion classification model"""
        try:
            print(f"🚀 Loading Hugging Face model: {self.model_name}")
            
            # Initialize the emotion classification pipeline
            self.classifier = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,  # Return all emotions with scores
                device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
                max_length=512,
                truncation=True
            )
            
            self.model_loaded = True
            print(f"✅ Hugging Face model '{self.model_name}' loaded successfully")
            print(f"✅ Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
            print(f"✅ Supported emotions: {list(self.emotion_mapping.values())}")
            
        except Exception as e:
            print(f"❌ Failed to load Hugging Face model: {str(e)}")
            self.model_loaded = False
            self.classifier = None
            raise RuntimeError(f"Hugging Face model failed to load: {str(e)}")
    
    def analyze_emotion(self, text: str) -> Dict[str, float]:
        """Analyze emotions using Hugging Face transformer model"""
        if not self.model_loaded or not self.classifier:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Emotion analysis model is not available. Please check if the Hugging Face model is properly loaded."
            )
        
        try:
            # Validate input text
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            # Clean and preprocess text
            cleaned_text = self.preprocess_text(text)
            
            # Get emotion predictions from Hugging Face model
            results = self.classifier(cleaned_text, padding=True, truncation=True)[0]
            
            # Convert to our emotion format and mapping
            emotions = {}
            for result in results:
                original_emotion = result['label']
                mapped_emotion = self.emotion_mapping.get(original_emotion, 'neutral')
                emotions[mapped_emotion] = float(result['score'])
            
            # Ensure all emotions are present with at least minimal scores
            for emotion in self.emotion_mapping.values():
                if emotion not in emotions:
                    emotions[emotion] = 0.0
            
            # Normalize scores to ensure they sum to 1 (handling any floating point issues)
            total_score = sum(emotions.values())
            if total_score > 0:
                emotions = {emotion: score / total_score for emotion, score in emotions.items()}
            
            return emotions
            
        except Exception as e:
            print(f"❌ Emotion analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Emotion analysis failed: {str(e)}"
            )
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better analysis"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Truncate very long texts to prevent memory issues
        if len(text) > 1000:
            text = text[:1000] + "..."
            
        return text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "model_loaded": self.model_loaded,
            "supported_emotions": list(self.emotion_mapping.values()),
            "original_emotions": self.supported_emotions,
            "device": "GPU" if torch.cuda.is_available() else "CPU",
            "framework": "Transformers",
            "model_type": "DistilRoBERTa-base"
        }

# Global analyzer instance
try:
    text_analyzer = HuggingFaceEmotionAnalyzer()
except Exception as e:
    print(f"❌ Critical: Failed to initialize emotion analyzer: {e}")
    text_analyzer = None

# Database helper functions
def save_emotion_result(db: Session, user_id: str, text: str, emotions: Dict[str, float], 
                       dominant_emotion: str, confidence: float, language: str = "en", 
                       session_id: Optional[str] = None):
    """Save emotion analysis result to database"""
    db_result = TextEmotionResult(
        user_id=user_id,
        text_content=text,
        emotions=json.dumps(emotions),
        dominant_emotion=dominant_emotion,
        confidence=confidence,
        language=language,
        text_length=len(text),
        word_count=len(text.split()),
        session_id=session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_user_results(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """Get paginated results for a user"""
    return db.query(TextEmotionResult).filter(
        TextEmotionResult.user_id == user_id
    ).order_by(
        TextEmotionResult.timestamp.desc()
    ).offset(skip).limit(limit).all()

def get_result_by_id(db: Session, result_id: int, user_id: str):
    """Get a specific result by ID for a user"""
    return db.query(TextEmotionResult).filter(
        TextEmotionResult.id == result_id,
        TextEmotionResult.user_id == user_id
    ).first()

def get_user_sessions(db: Session, user_id: str, start_date: Optional[date] = None, 
                     end_date: Optional[date] = None):
    """Get date-wise sessions for a user"""
    query = db.query(
        TextEmotionResult.analysis_date,
        TextEmotionResult.session_id,
        func.count(TextEmotionResult.id).label('total_analyses')
    ).filter(
        TextEmotionResult.user_id == user_id
    )
    
    if start_date:
        query = query.filter(TextEmotionResult.analysis_date >= start_date)
    if end_date:
        query = query.filter(TextEmotionResult.analysis_date <= end_date)
    
    sessions = query.group_by(
        TextEmotionResult.analysis_date, 
        TextEmotionResult.session_id
    ).order_by(
        TextEmotionResult.analysis_date.desc()
    ).all()
    
    return sessions

def get_session_details(db: Session, user_id: str, session_date: date, session_id: Optional[str] = None):
    """Get detailed analysis for a specific session"""
    query = db.query(TextEmotionResult).filter(
        TextEmotionResult.user_id == user_id,
        TextEmotionResult.analysis_date == session_date
    )
    
    if session_id:
        query = query.filter(TextEmotionResult.session_id == session_id)
    
    analyses = query.order_by(TextEmotionResult.timestamp.desc()).all()
    
    if not analyses:
        return None, None
    
    # Calculate session summary
    emotion_counts = {}
    total_confidence = 0
    total_text_length = 0
    total_word_count = 0
    dominant_emotions = []
    
    for analysis in analyses:
        emotion_counts[analysis.dominant_emotion] = emotion_counts.get(analysis.dominant_emotion, 0) + 1
        total_confidence += analysis.confidence
        total_text_length += analysis.text_length
        total_word_count += analysis.word_count
        
        dominant_emotions.append({
            "emotion": analysis.dominant_emotion,
            "confidence": analysis.confidence,
            "timestamp": analysis.timestamp.isoformat()
        })
    
    dominant_emotions.sort(key=lambda x: x["confidence"], reverse=True)
    
    summary = SessionSummary(
        session_date=session_date.isoformat(),
        session_id=session_id,
        total_analyses=len(analyses),
        emotion_distribution=emotion_counts,
        average_confidence=total_confidence / len(analyses),
        dominant_emotions=dominant_emotions[:5],
        text_statistics={
            "average_text_length": total_text_length / len(analyses),
            "average_word_count": total_word_count / len(analyses),
            "total_characters_analyzed": total_text_length,
            "total_words_analyzed": total_word_count
        }
    )
    
    return analyses, summary

def get_user_summary(db: Session, user_id: str, days: int = 30):
    """Get summary report for a user"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(TextEmotionResult).filter(
        TextEmotionResult.user_id == user_id,
        TextEmotionResult.timestamp >= start_date
    ).all()
    
    if not results:
        return None
    
    emotion_counts = {}
    total_confidence = 0
    total_text_length = 0
    total_word_count = 0
    
    for result in results:
        emotion_counts[result.dominant_emotion] = emotion_counts.get(result.dominant_emotion, 0) + 1
        total_confidence += result.confidence
        total_text_length += result.text_length
        total_word_count += result.word_count
    
    most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "neutral"
    
    return {
        "total_analyses": len(results),
        "emotion_distribution": emotion_counts,
        "average_confidence": total_confidence / len(results),
        "most_common_emotion": most_common_emotion,
        "text_statistics": {
            "average_text_length": total_text_length / len(results),
            "average_word_count": total_word_count / len(results),
            "total_characters_analyzed": total_text_length,
            "total_words_analyzed": total_word_count
        }
    }

# API Endpoints
@router.post("/analyze-text", response_model=EmotionAnalysisResponse)
async def analyze_text_emotion(request: TextAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze emotions from text using Hugging Face transformer model
    """
    try:
        # Validate text length
        if len(request.text.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text must be at least 3 characters long"
            )
        
        if len(request.text.strip()) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is too long. Maximum 5000 characters allowed."
            )
        
        # Check if analyzer is available
        if not text_analyzer or not text_analyzer.model_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Emotion analysis service is currently unavailable. Please try again later."
            )
        
        # Analyze emotions using Hugging Face model
        emotion_probabilities = text_analyzer.analyze_emotion(request.text)
        
        # Find dominant emotion
        dominant_emotion = max(emotion_probabilities.items(), key=lambda x: x[1])
        
        # Save to database
        db_result = save_emotion_result(
            db=db,
            user_id=request.user_id,
            text=request.text,
            emotions=emotion_probabilities,
            dominant_emotion=dominant_emotion[0],
            confidence=dominant_emotion[1],
            language=request.language,
            session_id=request.session_id
        )
        
        # Prepare metadata
        metadata = {
            "text_length": len(request.text),
            "word_count": len(request.text.split()),
            "language": request.language,
            "analysis_method": "Hugging Face Transformer",
            "model_used": text_analyzer.model_name,
            "confidence_metrics": {
                "dominant_emotion_confidence": dominant_emotion[1],
                "emotion_distribution": emotion_probabilities
            }
        }
        
        return EmotionAnalysisResponse(
            id=db_result.id,
            emotions=emotion_probabilities,
            dominant_emotion=dominant_emotion[0],
            confidence=dominant_emotion[1],
            timestamp=db_result.timestamp.isoformat(),
            user_id=request.user_id,
            metadata=metadata,
            text_preview=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            session_id=db_result.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {str(e)}"
        )

@router.get("/sessions", response_model=DateSessionResponse)
async def get_user_sessions_api(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db)
):
    """
    Get date-wise sessions for a user with summaries
    """
    try:
        sessions_data = get_user_sessions(db, user_id, start_date, end_date)
        
        sessions = []
        total_analyses = 0
        
        for session in sessions_data:
            analyses, summary = get_session_details(
                db, user_id, session.analysis_date, session.session_id
            )
            
            if summary:
                sessions.append(summary)
                total_analyses += session.total_analyses
        
        return DateSessionResponse(
            sessions=sessions,
            total_sessions=len(sessions),
            total_analyses=total_analyses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )

@router.get("/session-details", response_model=SessionDetailsResponse)
async def get_session_details_api(
    user_id: str = Query(..., description="User ID"),
    session_date: date = Query(..., description="Session date"),
    session_id: Optional[str] = Query(None, description="Specific session ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis for a specific session
    """
    analyses, summary = get_session_details(db, user_id, session_date, session_id)
    
    if not analyses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    analysis_responses = []
    for analysis in analyses:
        analysis_responses.append(TextEmotionResultResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            text_preview=analysis.text_content[:100] + "..." if len(analysis.text_content) > 100 else analysis.text_content,
            emotions=json.loads(analysis.emotions),
            dominant_emotion=analysis.dominant_emotion,
            confidence=analysis.confidence,
            analysis_type=analysis.analysis_type,
            timestamp=analysis.timestamp.isoformat(),
            analysis_date=analysis.analysis_date.isoformat(),
            text_length=analysis.text_length,
            word_count=analysis.word_count,
            language=analysis.language,
            session_id=analysis.session_id
        ))
    
    return SessionDetailsResponse(
        session_date=session_date.isoformat(),
        session_id=session_id,
        analyses=analysis_responses,
        summary=summary
    )

@router.get("/results", response_model=PaginatedResults)
async def get_analysis_results(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get paginated analysis results for a user
    """
    try:
        skip = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(TextEmotionResult).filter(
            TextEmotionResult.user_id == user_id
        ).count()
        
        # Get paginated results
        db_results = get_user_results(db, user_id, skip, page_size)
        
        results = []
        for result in db_results:
            results.append(TextEmotionResultResponse(
                id=result.id,
                user_id=result.user_id,
                text_preview=result.text_content[:100] + "..." if len(result.text_content) > 100 else result.text_content,
                emotions=json.loads(result.emotions),
                dominant_emotion=result.dominant_emotion,
                confidence=result.confidence,
                analysis_type=result.analysis_type,
                timestamp=result.timestamp.isoformat(),
                analysis_date=result.analysis_date.isoformat(),
                text_length=result.text_length,
                word_count=result.word_count,
                language=result.language,
                session_id=result.session_id
            ))
        
        return PaginatedResults(
            results=results,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch results: {str(e)}"
        )

@router.get("/summary", response_model=SummaryReport)
async def get_analysis_summary(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days for summary"),
    db: Session = Depends(get_db)
):
    """
    Get summary report for a user's analyses
    """
    summary = get_user_summary(db, user_id, days)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis data found for the specified period"
        )
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return SummaryReport(
        user_id=user_id,
        period=f"last_{days}_days",
        total_analyses=summary["total_analyses"],
        emotion_distribution=summary["emotion_distribution"],
        average_confidence=summary["average_confidence"],
        most_common_emotion=summary["most_common_emotion"],
        text_statistics=summary["text_statistics"],
        timeframe={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )

@router.get("/export")
async def export_analysis_results(
    user_id: str = Query(..., description="User ID"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    db: Session = Depends(get_db)
):
    """
    Export analysis results in JSON or CSV format
    """
    try:
        results = db.query(TextEmotionResult).filter(
            TextEmotionResult.user_id == user_id
        ).order_by(TextEmotionResult.timestamp.desc()).all()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results found to export"
            )
        
        export_data = []
        for result in results:
            export_data.append({
                "id": result.id,
                "user_id": result.user_id,
                "text_preview": result.text_content[:100] + "..." if len(result.text_content) > 100 else result.text_content,
                "emotions": json.loads(result.emotions),
                "dominant_emotion": result.dominant_emotion,
                "confidence": result.confidence,
                "analysis_type": result.analysis_type,
                "timestamp": result.timestamp.isoformat(),
                "text_length": result.text_length,
                "word_count": result.word_count,
                "language": result.language,
                "session_id": result.session_id
            })
        
        if format == "csv":
            # Flatten emotions for CSV
            csv_data = []
            for item in export_data:
                csv_row = {k: v for k, v in item.items() if k != 'emotions'}
                for emotion, score in item['emotions'].items():
                    csv_row[f'emotion_{emotion}'] = score
                csv_data.append(csv_row)
            
            df = pd.DataFrame(csv_data)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            return ExportResponse(
                filename=f"text_emotion_analysis_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                content=csv_buffer.getvalue(),
                format="csv"
            )
        else:
            return ExportResponse(
                filename=f"text_emotion_analysis_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                content=export_data,
                format="json"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/text-model-status", response_model=ModelStatusResponse)
async def get_text_model_status():
    """Get status of text emotion analysis model"""
    if text_analyzer:
        model_info = text_analyzer.get_model_info()
        return ModelStatusResponse(
            model_loaded=model_info["model_loaded"],
            supported_emotions=model_info["supported_emotions"],
            supported_languages=["en"],
            analysis_methods=["Hugging Face Transformer"],
            status="active" if model_info["model_loaded"] else "inactive",
            database_connected=True,
            model_name=model_info["model_name"],
            device=model_info["device"]
        )
    else:
        return ModelStatusResponse(
            model_loaded=False,
            supported_emotions=[],
            supported_languages=[],
            analysis_methods=[],
            status="inactive",
            database_connected=True,
            model_name="N/A",
            device="N/A"
        )