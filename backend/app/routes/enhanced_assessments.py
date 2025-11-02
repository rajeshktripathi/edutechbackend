# app/routers/enhanced_assessments.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models.enhanced_assessment_models import Base, EnhancedAssessmentType, EnhancedAssessmentSession, EnhancedQuestion, EnhancedVideoRecording, MockVideoAnalysis, EnhancedAssessmentResponse
from app.services.enhanced_assessment_service import EnhancedAssessmentService

router = APIRouter(prefix="/api/v1/assessments", tags=["enhanced-assessments"])

@router.get("/types")
async def get_assessment_types(db: Session = Depends(get_db)):
    """Get all available assessment types"""
    try:
        types = db.query(EnhancedAssessmentType).filter(
            EnhancedAssessmentType.is_active == True
        ).all()
        
        # If no types exist, initialize sample data
        if not types:
            EnhancedAssessmentService.initialize_assessment_data(db)
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
        raise HTTPException(status_code=500, detail=f"Error getting assessment types: {str(e)}")

@router.post("/sessions/start")
async def start_assessment_session(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Start a new assessment session"""
    try:
        user_id = data.get("user_id", 1)  # In real app, get from auth
        assessment_type_id = data.get("assessment_type_id")
        
        if not assessment_type_id:
            raise HTTPException(status_code=400, detail="Assessment type ID is required")
        
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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

@router.post("/sessions/{session_id}/submit")
async def submit_assessment_session(
    session_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit assessment responses and process results"""
    try:
        responses = data.get("responses", [])
        video_settings = data.get("video_settings", {})
        
        if not responses:
            raise HTTPException(status_code=400, detail="No responses provided")
        
        # Submit responses and calculate scores
        result = EnhancedAssessmentService.submit_assessment_responses(
            db, session_id, responses
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Create video recording entry (mock for now)
        recording = EnhancedVideoRecording(
            session_id=session_id,
            video_file_path="/mock/path/to/video.webm",
            video_duration_seconds=300,
            file_size_bytes=1024000,
            processing_status="completed",
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
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "score": result["total_score"],
                "max_score": result["max_score"],
                "percentage": result["percentage"],
                "time_taken": result["time_taken"],
                "recording_id": recording.id,
                "analysis_id": mock_analysis.id
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting assessment: {str(e)}")

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
        
        # Get responses
        responses = db.query(EnhancedAssessmentResponse).filter(
            EnhancedAssessmentResponse.session_id == session_id
        ).all()
        
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
                    "id": assessment_type.id if assessment_type else None,
                    "name": assessment_type.name if assessment_type else "Unknown Assessment",
                    "category": assessment_type.category if assessment_type else "General",
                    "description": assessment_type.description if assessment_type else ""
                },
                "responses": [
                    {
                        "question_id": response.question_id,
                        "user_answer": response.user_answer,
                        "is_correct": response.is_correct,
                        "points_earned": response.points_earned
                    }
                    for response in responses
                ],
                "video_analysis": {
                    "emotional_analysis": video_analysis.emotional_analysis if video_analysis else {},
                    "mood_score": video_analysis.mood_score if video_analysis else 0.0,
                    "dominant_emotion": video_analysis.dominant_emotion if video_analysis else "neutral",
                    "engagement_level": video_analysis.engagement_level if video_analysis else 0.0,
                    "focus_score": video_analysis.focus_score if video_analysis else 0.0,
                    "confidence_level": video_analysis.confidence_level if video_analysis else 0.0,
                    "motivation_level": video_analysis.motivation_level if video_analysis else 0.0,
                    "personality_insights": video_analysis.personality_insights if video_analysis else {},
                    "attention_metrics": video_analysis.attention_metrics if video_analysis else {},
                    "cognitive_analysis": video_analysis.cognitive_analysis if video_analysis else {},
                    "problem_solving_style": video_analysis.problem_solving_style if video_analysis else "analytical",
                    "career_predictions": video_analysis.career_predictions if video_analysis else {},
                    "overall_score": video_analysis.overall_score if video_analysis else 0.0,
                    "analysis_remarks": video_analysis.analysis_remarks if video_analysis else "No analysis available"
                },
                "video_recording": {
                    "id": video_recording.id if video_recording else None,
                    "processing_status": video_recording.processing_status if video_recording else "not_available",
                    "download_available": video_recording and video_recording.video_file_path is not None
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session results: {str(e)}")

@router.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get all assessment sessions for a user"""
    try:
        sessions = db.query(EnhancedAssessmentSession).filter(
            EnhancedAssessmentSession.user_id == user_id
        ).order_by(EnhancedAssessmentSession.started_at.desc()).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": session.id,
                    "session_code": session.session_code,
                    "assessment_type_id": session.assessment_type_id,
                    "status": session.status,
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
        raise HTTPException(status_code=500, detail=f"Error getting user sessions: {str(e)}")

@router.post("/initialize-data")
async def initialize_assessment_data(db: Session = Depends(get_db)):
    """Initialize sample assessment data (for development)"""
    try:
        EnhancedAssessmentService.initialize_assessment_data(db)
        return {
            "success": True, 
            "message": "Assessment data initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing data: {str(e)}")

@router.get("/types/{assessment_type_id}/questions")
async def get_assessment_questions(assessment_type_id: int, db: Session = Depends(get_db)):
    """Get questions for a specific assessment type"""
    try:
        questions = db.query(EnhancedQuestion).filter(
            EnhancedQuestion.assessment_type_id == assessment_type_id,
            EnhancedQuestion.is_active == True
        ).order_by(EnhancedQuestion.order_index).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "options": q.options,
                    "points": q.points,
                    "order_index": q.order_index
                }
                for q in questions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")