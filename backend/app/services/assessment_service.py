from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime

from app.models.assessment_models import (
    AssessmentType, Question, AssessmentSession, 
    AssessmentResponse, VideoRecording, VideoAnalysisResult,
    AssessmentSessionCreate, AssessmentResponseCreate
)

class AssessmentService:
    
    @staticmethod
    def get_all_assessment_types(db: Session, active_only: bool = True) -> List[AssessmentType]:
        query = db.query(AssessmentType)
        if active_only:
            query = query.filter(AssessmentType.is_active == True)
        return query.order_by(AssessmentType.name).all()
    
    @staticmethod
    def get_assessment_type_by_id(db: Session, assessment_type_id: int) -> Optional[AssessmentType]:
        return db.query(AssessmentType).filter(AssessmentType.id == assessment_type_id).first()
    
    @staticmethod
    def get_questions_by_assessment(db: Session, assessment_type_id: int) -> List[Question]:
        return db.query(Question).filter(
            Question.assessment_type_id == assessment_type_id,
            Question.is_active == True
        ).order_by(Question.order_index).all()
    
    @staticmethod
    def create_assessment_session(
        db: Session, 
        user_id: int, 
        assessment_type_id: int
    ) -> AssessmentSession:
        session = AssessmentSession(
            user_id=user_id,
            assessment_type_id=assessment_type_id,
            status="in_progress"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def save_assessment_responses(
        db: Session,
        session_id: int,
        responses: List[AssessmentResponseCreate]
    ) -> List[AssessmentResponse]:
        saved_responses = []
        for response_data in responses:
            response = AssessmentResponse(
                session_id=session_id,
                question_id=response_data.question_id,
                user_answer=response_data.user_answer,
                response_time_seconds=response_data.response_time_seconds
            )
            db.add(response)
            saved_responses.append(response)
        
        db.commit()
        for response in saved_responses:
            db.refresh(response)
        return saved_responses
    
    @staticmethod
    def complete_assessment_session(
        db: Session,
        session_id: int,
        total_score: float,
        max_score: float
    ) -> AssessmentSession:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
        if not session:
            raise ValueError("Assessment session not found")
        
        session.status = "completed"
        session.completed_at = datetime.now()
        session.total_score = total_score
        session.max_score = max_score
        session.percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Calculate time taken
        if session.started_at and session.completed_at:
            time_taken = (session.completed_at - session.started_at).total_seconds()
            session.time_taken_seconds = int(time_taken)
        
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def save_video_recording(
        db: Session,
        session_id: int,
        video_file_path: str,
        video_duration: int,
        file_size: int,
        recording_started: datetime,
        recording_ended: datetime
    ) -> VideoRecording:
        recording = VideoRecording(
            session_id=session_id,
            video_file_path=video_file_path,
            video_duration_seconds=video_duration,
            file_size_bytes=file_size,
            recording_started_at=recording_started,
            recording_ended_at=recording_ended,
            processing_status="pending"
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)
        return recording
    
    @staticmethod
    def get_video_analysis_by_recording_id(db: Session, recording_id: int) -> Optional[VideoAnalysisResult]:
        return db.query(VideoAnalysisResult).filter(
            VideoAnalysisResult.video_recording_id == recording_id
        ).first()
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[AssessmentSession]:
        return db.query(AssessmentSession).filter(
            AssessmentSession.user_id == user_id
        ).order_by(AssessmentSession.started_at.desc()).all()

class VideoAnalysisService:
    
    @staticmethod
    def analyze_video_mock(video_path: str) -> Dict[str, Any]:
        """
        Mock video analysis service that returns simulated analysis results.
        In production, this would integrate with actual computer vision APIs.
        """
        # Simulate processing delay
        import time
        time.sleep(2)
        
        return {
            "emotional_analysis": {
                "happiness": 0.75,
                "sadness": 0.12,
                "anger": 0.08,
                "surprise": 0.25,
                "fear": 0.05,
                "disgust": 0.03,
                "neutral": 0.15
            },
            "mood_score": 0.72,
            "dominant_emotion": "happiness",
            "engagement_level": 0.85,
            "focus_score": 0.78,
            "confidence_level": 0.68,
            "personality_insights": {
                "openness": 0.82,
                "conscientiousness": 0.75,
                "extraversion": 0.60,
                "agreeableness": 0.70,
                "neuroticism": 0.35
            },
            "attention_metrics": {
                "gaze_stability": 0.80,
                "blink_rate": "normal",
                "head_movement": "moderate",
                "posture_consistency": 0.75
            },
            "cognitive_analysis": {
                "concentration_level": 0.82,
                "mental_workload": "moderate",
                "problem_solving_efficiency": 0.70,
                "decision_making_speed": "deliberate"
            },
            "problem_solving_style": "analytical",
            "overall_score": 0.76,
            "analysis_remarks": "User showed good engagement and positive emotional state throughout the assessment. Demonstrated analytical thinking patterns."
        }
    
    @staticmethod
    def process_video_analysis(
        db: Session,
        recording_id: int,
        video_path: str
    ) -> VideoAnalysisResult:
        # Update processing status
        recording = db.query(VideoRecording).filter(VideoRecording.id == recording_id).first()
        if recording:
            recording.processing_status = "processing"
            db.commit()
        
        try:
            # Perform mock analysis
            analysis_data = VideoAnalysisService.analyze_video_mock(video_path)
            
            # Save analysis results
            analysis = VideoAnalysisResult(
                video_recording_id=recording_id,
                emotional_analysis=analysis_data["emotional_analysis"],
                mood_score=analysis_data["mood_score"],
                dominant_emotion=analysis_data["dominant_emotion"],
                engagement_level=analysis_data["engagement_level"],
                focus_score=analysis_data["focus_score"],
                confidence_level=analysis_data["confidence_level"],
                personality_insights=analysis_data["personality_insights"],
                attention_metrics=analysis_data["attention_metrics"],
                cognitive_analysis=analysis_data["cognitive_analysis"],
                problem_solving_style=analysis_data["problem_solving_style"],
                overall_score=analysis_data["overall_score"],
                analysis_remarks=analysis_data["analysis_remarks"]
            )
            
            db.add(analysis)
            
            # Update recording status
            if recording:
                recording.processing_status = "completed"
            
            db.commit()
            db.refresh(analysis)
            return analysis
            
        except Exception as e:
            # Update recording status to failed
            if recording:
                recording.processing_status = "failed"
                db.commit()
            raise e