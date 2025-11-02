# services/api/enhanced_assessment_api.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models.enhanced_assessment_models import (
    EnhancedAssessmentType, EnhancedAssessmentSession, EnhancedQuestion,
    EnhancedVideoRecording, MockVideoAnalysis
)
from app.services.enhanced_assessment_service import EnhancedAssessmentService

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])

@router.get("/types")
async def get_assessment_types(db: Session = Depends(get_db)):
    """Get all available assessment types"""
    try:
        types = db.query(EnhancedAssessmentType).filter(
            EnhancedAssessmentType.is_active == True
        ).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": at.id,
                    "name": at.name,
                    "category": at.category,
                    "description": at.description,
                    "duration_minutes": at.duration_minutes,
                    "questions_count": at.questions_count,
                    "created_at": at.created_at.isoformat() if at.created_at else None
                }
                for at in types
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/start")
async def start_assessment_session(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Start a new assessment session"""
    try:
        user_id = data.get("user_id", 1)  # In real app, get from auth
        assessment_type_id = data.get("assessment_type_id")
        
        session = EnhancedAssessmentService.start_assessment_session(
            db, user_id, assessment_type_id
        )
        
        return {
            "success": True,
            "data": {
                "session": {
                    "id": session.id,
                    "session_code": session.session_code,
                    "user_id": session.user_id,
                    "assessment_type_id": session.assessment_type_id,
                    "status": session.status,
                    "started_at": session.started_at.isoformat() if session.started_at else None
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/submit")
async def submit_assessment_session(
    session_id: int,
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit assessment responses and process results"""
    try:
        responses = data.get("responses", [])
        video_settings = data.get("video_settings", {})
        
        # Submit responses and calculate scores
        result = EnhancedAssessmentService.submit_assessment_responses(
            db, session_id, responses
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Create video recording entry
        recording = EnhancedVideoRecording(
            session_id=session_id,
            processing_status="pending",
            recording_started_at=datetime.utcnow(),
            recording_ended_at=datetime.utcnow()
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)
        
        # Generate mock video analysis
        mock_analysis = EnhancedAssessmentService.generate_mock_video_analysis(
            session_id, recording.id
        )
        db.add(mock_analysis)
        db.commit()
        
        # Update recording status
        recording.processing_status = "completed"
        db.commit()
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "score": result["total_score"],
                "max_score": result["max_score"],
                "percentage": result["percentage"],
                "recording_id": recording.id,
                "analysis_id": mock_analysis.id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/results")
async def get_session_results(session_id: int, db: Session = Depends(get_db)):
    """Get complete session results including video analysis"""
    try:
        session = db.query(EnhancedAssessmentSession).filter(
            EnhancedAssessmentSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get assessment type
        assessment_type = db.query(EnhancedAssessmentType).filter(
            EnhancedAssessmentType.id == session.assessment_type_id
        ).first()
        
        # Get video analysis
        video_analysis = db.query(MockVideoAnalysis).filter(
            MockVideoAnalysis.session_id == session_id
        ).first()
        
        # Get video recording
        video_recording = db.query(EnhancedVideoRecording).filter(
            EnhancedVideoRecording.session_id == session_id
        ).first()
        
        return {
            "success": True,
            "data": {
                "session": {
                    "id": session.id,
                    "session_code": session.session_code,
                    "user_id": session.user_id,
                    "total_score": session.total_score,
                    "max_score": session.max_score,
                    "percentage": session.percentage,
                    "time_taken_seconds": session.time_taken_seconds,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None
                },
                "assessment_type": {
                    "id": assessment_type.id,
                    "name": assessment_type.name,
                    "category": assessment_type.category,
                    "description": assessment_type.description
                } if assessment_type else None,
                "video_analysis": {
                    "emotional_analysis": video_analysis.emotional_analysis if video_analysis else None,
                    "mood_score": video_analysis.mood_score if video_analysis else None,
                    "dominant_emotion": video_analysis.dominant_emotion if video_analysis else None,
                    "engagement_level": video_analysis.engagement_level if video_analysis else None,
                    "focus_score": video_analysis.focus_score if video_analysis else None,
                    "confidence_level": video_analysis.confidence_level if video_analysis else None,
                    "motivation_level": video_analysis.motivation_level if video_analysis else None,
                    "personality_insights": video_analysis.personality_insights if video_analysis else None,
                    "attention_metrics": video_analysis.attention_metrics if video_analysis else None,
                    "cognitive_analysis": video_analysis.cognitive_analysis if video_analysis else None,
                    "problem_solving_style": video_analysis.problem_solving_style if video_analysis else None,
                    "career_predictions": video_analysis.career_predictions if video_analysis else None,
                    "overall_score": video_analysis.overall_score if video_analysis else None,
                    "analysis_remarks": video_analysis.analysis_remarks if video_analysis else None
                } if video_analysis else None,
                "video_recording": {
                    "id": video_recording.id if video_recording else None,
                    "processing_status": video_recording.processing_status if video_recording else None,
                    "download_available": video_recording.download_path is not None if video_recording else False
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get all assessment sessions for a user"""
    try:
        sessions = db.query(EnhancedAssessmentSession).filter(
            EnhancedAssessmentSession.user_id == user_id,
            EnhancedAssessmentSession.status == "completed"
        ).order_by(EnhancedAssessmentSession.completed_at.desc()).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": session.id,
                    "session_code": session.session_code,
                    "assessment_type_id": session.assessment_type_id,
                    "total_score": session.total_score,
                    "max_score": session.max_score,
                    "percentage": session.percentage,
                    "time_taken_seconds": session.time_taken_seconds,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None
                }
                for session in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-data")
async def initialize_assessment_data(db: Session = Depends(get_db)):
    """Initialize sample assessment data (for development)"""
    try:
        EnhancedAssessmentService.initialize_assessment_data(db)
        return {"success": True, "message": "Assessment data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))