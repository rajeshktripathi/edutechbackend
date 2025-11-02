from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.models.user_models import User
from app.models.assessment_models import (
    AssessmentType, Question, AssessmentSession, AssessmentResponse,
    VideoRecording, VideoAnalysisResult,
    AssessmentTypeResponse, QuestionResponse, AssessmentSessionCreate,
    AssessmentResponseCreate, VideoAnalysisRequest, CompleteAssessmentResponse,
    AssessmentSessionResponse
)
from app.services.assessment_service import (
    AssessmentService, VideoAnalysisService, 
    VideoDownloadService, AssessmentResultsService
)
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
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
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
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
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
    recording_started: Optional[datetime] = None,
    recording_ended: Optional[datetime] = None,
    video_duration: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload video recording for an assessment session
    """
    # Verify session exists and belongs to current user
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
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
    
    # Set default timestamps if not provided
    if not recording_started:
        recording_started = datetime.now()
    if not recording_ended:
        recording_ended = datetime.now()
    if not video_duration:
        # Calculate duration from timestamps
        video_duration = int((recording_ended - recording_started).total_seconds())
    
    # Save video recording metadata
    recording = AssessmentService.save_video_recording(
        db=db,
        session_id=session_id,
        video_file_path=file_path,
        video_duration=video_duration,
        file_size=len(contents),
        recording_started_at=recording_started,
        recording_ended_at=recording_ended
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
        "processing_status": recording.processing_status,
        "video_duration": video_duration
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
    session = AssessmentService.get_session_by_id(db, recording.session_id, current_user.id)
    
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
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Get video recording for this session
    recording = AssessmentService.get_video_recording_by_session(db, session_id)
    
    if not recording:
        return {"video_available": False, "message": "No video recording found for this session"}
    
    # Get analysis results
    analysis = VideoAnalysisService.get_video_analysis_results(db, session_id)
    
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

@router.get("/sessions/{session_id}/complete-result")
def get_complete_session_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete assessment session result including video analysis
    """
    # Verify session exists and belongs to current user
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Get comprehensive results using the new service
    results = AssessmentResultsService.get_comprehensive_results(db, session_id, current_user.id)
    
    if "error" in results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=results["error"]
        )
    
    return results

@router.post("/sessions/{session_id}/download-video")
async def download_video_recording(
    session_id: int,
    download_folder: Optional[str] = Query(None, description="Custom folder path to save the video"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download video recording to user-specified folder location
    """
    # Prepare video for download
    download_prep = VideoDownloadService.prepare_video_for_download(db, session_id, current_user.id)
    
    if not download_prep["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=download_prep["error"]
        )
    
    file_info = download_prep["file_info"]
    
    try:
        # Save video to user-specified location
        destination_path = AssessmentService.save_video_to_user_location(
            db, file_info["recording_id"], download_folder
        )
        
        return {
            "message": "Video downloaded successfully",
            "destination_path": destination_path,
            "file_info": file_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download video: {str(e)}"
        )

@router.get("/sessions/{session_id}/video-download-info")
def get_video_download_info(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get video download information and history
    """
    # Verify session exists and belongs to current user
    session = AssessmentService.get_session_by_id(db, session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found"
        )
    
    # Get download preparation info
    download_prep = VideoDownloadService.prepare_video_for_download(db, session_id, current_user.id)
    
    # Get download history
    download_history = VideoDownloadService.get_video_download_history(db, session_id)
    
    return {
        "download_available": download_prep["success"],
        "file_info": download_prep.get("file_info"),
        "download_history": download_history,
        "error": download_prep.get("error")
    }

@router.delete("/sessions/{session_id}")
def delete_assessment_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an assessment session and all associated data
    """
    success = AssessmentService.delete_assessment_session(db, session_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found or access denied"
        )
    
    return {"message": "Assessment session deleted successfully"}

@router.get("/video-recordings/{recording_id}/status")
def get_video_processing_status(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get video processing status
    """
    recording = db.query(VideoRecording).filter(VideoRecording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video recording not found"
        )
    
    # Verify the recording belongs to the current user
    session = AssessmentService.get_session_by_id(db, recording.session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this recording"
        )
    
    analysis = AssessmentService.get_video_analysis_by_recording_id(db, recording_id)
    
    return {
        "recording_id": recording_id,
        "processing_status": recording.processing_status,
        "analysis_available": analysis is not None,
        "error_message": recording.error_message
    }

@router.get("/instructions/{assessment_type_id}")
def get_assessment_instructions(
    assessment_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assessment instructions and guidelines
    """
    assessment_type = AssessmentService.get_assessment_type_by_id(db, assessment_type_id)
    if not assessment_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment type not found"
        )
    
    # Return structured instructions
    instructions = {
        "assessment_type": assessment_type.name,
        "duration_minutes": assessment_type.duration_minutes,
        "questions_count": assessment_type.questions_count,
        "instructions": [
            {
                "title": "Read Questions Carefully",
                "description": "Take your time to understand each question before answering.",
                "icon": "📝"
            },
            {
                "title": "Time Management",
                "description": f"This assessment will take approximately {assessment_type.duration_minutes} minutes.",
                "icon": "⏱️"
            },
            {
                "title": "Video Recording",
                "description": "Your responses will be recorded via webcam for analysis. Make sure you're in a well-lit environment.",
                "icon": "🎥"
            },
            {
                "title": "Privacy & Security",
                "description": "Your video is recorded locally and only uploaded when you submit. You can download your video after completion.",
                "icon": "🔒"
            },
            {
                "title": "Tips for Best Results",
                "description": "Ensure stable internet connection, use a quiet environment, keep your face well-lit and visible, and answer honestly and naturally.",
                "icon": "💡"
            }
        ],
        "technical_requirements": [
            "Stable internet connection",
            "Webcam and microphone access",
            "Modern web browser (Chrome, Firefox, Safari, Edge)",
            "Minimum 5MB free storage for video download"
        ]
    }
    
    return instructions