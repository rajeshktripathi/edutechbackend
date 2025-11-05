from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user_models import User
from app.models.assessment_models import (
    AssessmentType, Question, AssessmentSession, AssessmentResponse,
    VideoRecording, VideoAnalysisResult,
    AssessmentTypeResponse, QuestionResponse, AssessmentSessionCreate,
    AssessmentResponseCreate, VideoAnalysisRequest, CompleteAssessmentResponse,
    AssessmentSessionResponse  # Add this import
)
from app.services.assessment_service import AssessmentService, VideoAnalysisService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])

# Configuration
UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/types", response_model=List[AssessmentTypeResponse])
def get_assessment_types(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available assessment types
    """
    assessment_types = AssessmentService.get_all_assessment_types(db, active_only)
    return assessment_types

@router.get("/types/{assessment_type_id}", response_model=AssessmentTypeResponse)
def get_assessment_type(
    assessment_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific assessment type details
    """
    assessment_type = AssessmentService.get_assessment_type_by_id(db, assessment_type_id)
    if not assessment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment type not found"
        )
    return assessment_type

@router.get("/types/{assessment_type_id}/questions", response_model=List[QuestionResponse])
def get_assessment_questions(
    assessment_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get questions for a specific assessment type
    """
    # Verify assessment type exists
    assessment_type = AssessmentService.get_assessment_type_by_id(db, assessment_type_id)
    if not assessment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment type not found"
        )
    
    questions = AssessmentService.get_questions_by_assessment(db, assessment_type_id)
    return questions

@router.post("/sessions", response_model=AssessmentSessionResponse)
def create_assessment_session(
    session_data: AssessmentSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new assessment session
    """
    # Verify assessment type exists
    assessment_type = AssessmentService.get_assessment_type_by_id(db, session_data.assessment_type_id)
    if not assessment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment type not found"
        )
    
    session = AssessmentService.create_assessment_session(
        db, current_user.id, session_data.assessment_type_id
    )
    return session

@router.post("/sessions/{session_id}/responses")
def submit_assessment_responses(
    session_id: int,
    responses: List[AssessmentResponseCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit responses for an assessment session
    """
    # Verify session exists and belongs to current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    saved_responses = AssessmentService.save_assessment_responses(db, session_id, responses)
    return {"message": "Responses saved successfully", "count": len(saved_responses)}

@router.post("/sessions/{session_id}/complete")
def complete_assessment_session(
    session_id: int,
    total_score: float,
    max_score: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark assessment session as completed with final scores
    """
    # Verify session exists and belongs to current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    completed_session = AssessmentService.complete_assessment_session(
        db, session_id, total_score, max_score
    )
    return completed_session

@router.post("/sessions/{session_id}/upload-video")
async def upload_assessment_video(
    session_id: int,
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    process_automatically: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload video recording for an assessment session
    """
    # Verify session exists and belongs to current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Generate unique filename
    file_extension = video_file.filename.split('.')[-1] if '.' in video_file.filename else 'webm'
    unique_filename = f"{current_user.id}_{session_id}_{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save video file
    try:
        contents = await video_file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save video file: {str(e)}"
        )
    
    # Save video recording metadata
    recording = AssessmentService.save_video_recording(
        db=db,
        session_id=session_id,
        video_file_path=file_path,
        video_duration=0,  # Would need to calculate from video metadata
        file_size=len(contents),
        recording_started_at=datetime.now(),  # Should be passed from frontend
        recording_ended_at=datetime.now()     # Should be passed from frontend
    )
    
    # Process video analysis if automatic processing is enabled
    if process_automatically:
        background_tasks.add_task(
            VideoAnalysisService.process_video_analysis,
            db, recording.id, file_path
        )
    
    return {
        "message": "Video uploaded successfully",
        "recording_id": recording.id,
        "file_path": file_path,
        "processing_status": recording.processing_status
    }

@router.post("/video-recordings/{recording_id}/analyze")
def analyze_video_recording(
    recording_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger video analysis for a recording
    """
    recording = db.query(VideoRecording).filter(VideoRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video recording not found"
        )
    
    # Verify the recording belongs to the current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == recording.session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this recording"
        )
    
    # Start background analysis
    background_tasks.add_task(
        VideoAnalysisService.process_video_analysis,
        db, recording_id, recording.video_file_path
    )
    
    return {"message": "Video analysis started", "recording_id": recording_id}

@router.get("/sessions/{session_id}/video-analysis")
def get_video_analysis(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get video analysis results for a session
    """
    # Verify session exists and belongs to current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Get video recording for this session
    recording = db.query(VideoRecording).filter(
        VideoRecording.session_id == session_id
    ).first()
    
    if not recording:
        return {"video_available": False, "message": "No video recording found for this session"}
    
    # Get analysis results
    analysis = AssessmentService.get_video_analysis_by_recording_id(db, recording.id)
    
    return {
        "video_available": True,
        "recording": recording,
        "analysis": analysis,
        "processing_status": recording.processing_status
    }

@router.get("/sessions/user", response_model=List[AssessmentSessionResponse])
def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all assessment sessions for the current user
    """
    sessions = AssessmentService.get_user_sessions(db, current_user.id)
    return sessions

@router.get("/sessions/{session_id}/complete-result", response_model=CompleteAssessmentResponse)
def get_complete_session_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete assessment session result including video analysis
    """
    # Verify session exists and belongs to current user
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Get assessment type
    assessment_type = AssessmentService.get_assessment_type_by_id(db, session.assessment_type_id)
    
    # Get video recording and analysis
    recording = db.query(VideoRecording).filter(
        VideoRecording.session_id == session_id
    ).first()
    
    video_analysis = None
    if recording:
        video_analysis = AssessmentService.get_video_analysis_by_recording_id(db, recording.id)
    
    return {
        "session": session,
        "assessment_type": assessment_type,
        "video_analysis": video_analysis
    }