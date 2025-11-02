# app/services/enhanced_assessment_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import random

from app.models.enhanced_assessment_models import (
    EnhancedAssessmentType, EnhancedQuestion, EnhancedAssessmentSession,
    EnhancedAssessmentResponse, EnhancedVideoRecording, MockVideoAnalysis
)

class EnhancedAssessmentService:
    
    @staticmethod
    def initialize_assessment_data(db: Session):
        """Initialize sample assessment data"""
        try:
            # Check if data already exists
            existing_types = db.query(EnhancedAssessmentType).count()
            if existing_types > 0:
                print("Assessment data already exists")
                return
            
            print("Initializing enhanced assessment data...")
            
            # Create assessment types
            assessment_types = [
                EnhancedAssessmentType(
                    name="Psychology Personality Test",
                    category="Psychology",
                    description="Comprehensive personality assessment based on psychological principles",
                    duration_minutes=15,
                    questions_count=5
                ),
                EnhancedAssessmentType(
                    name="Career Interest Inventory", 
                    category="Career",
                    description="Discover your ideal career path based on interests and aptitudes",
                    duration_minutes=20,
                    questions_count=5
                ),
                EnhancedAssessmentType(
                    name="Technical Skills Assessment",
                    category="Skills", 
                    description="Evaluate your technical and soft skills for career development",
                    duration_minutes=25,
                    questions_count=5
                )
            ]
            
            for assessment_type in assessment_types:
                db.add(assessment_type)
            
            db.flush()  # Get IDs for the assessment types
            
            # Create questions for each assessment type
            questions_data = [
                # Psychology Questions
                {
                    "assessment_type": assessment_types[0],
                    "questions": [
                        {
                            "question_text": "How do you typically react in social situations?",
                            "options": ["Very outgoing and sociable", "Comfortable with small groups", "Prefer one-on-one interactions", "Rather be alone"],
                            "correct_answer": "Comfortable with small groups",
                            "points": 1,
                            "order_index": 1
                        },
                        {
                            "question_text": "When facing challenges, you usually:",
                            "options": ["Plan carefully before acting", "Jump right in and adapt", "Seek advice from others", "Avoid if possible"],
                            "correct_answer": "Plan carefully before acting", 
                            "points": 1,
                            "order_index": 2
                        },
                        {
                            "question_text": "How important is routine in your daily life?",
                            "options": ["Very important - I stick to schedules", "Somewhat important", "Flexible but like some structure", "Prefer spontaneity"],
                            "correct_answer": "Flexible but like some structure",
                            "points": 1,
                            "order_index": 3
                        },
                        {
                            "question_text": "When making decisions, you rely more on:",
                            "options": ["Logic and facts", "Intuition and feelings", "Past experiences", "Others' opinions"],
                            "correct_answer": "Logic and facts",
                            "points": 1,
                            "order_index": 4
                        },
                        {
                            "question_text": "Your ideal work environment would be:",
                            "options": ["Structured and predictable", "Dynamic and changing", "Collaborative team setting", "Independent and quiet"],
                            "correct_answer": "Collaborative team setting",
                            "points": 1,
                            "order_index": 5
                        }
                    ]
                },
                # Career Questions
                {
                    "assessment_type": assessment_types[1],
                    "questions": [
                        {
                            "question_text": "Which activity interests you most?",
                            "options": ["Solving technical problems", "Helping and teaching others", "Creating art or designs", "Analyzing data and trends"],
                            "correct_answer": "Solving technical problems",
                            "points": 1,
                            "order_index": 1
                        },
                        {
                            "question_text": "Your preferred work setting is:",
                            "options": ["Office environment", "Outdoor/field work", "Remote/flexible", "Laboratory/research facility"],
                            "correct_answer": "Office environment",
                            "points": 1,
                            "order_index": 2
                        },
                        {
                            "question_text": "What motivates you most in a job?",
                            "options": ["High salary and benefits", "Work-life balance", "Creative freedom", "Career advancement opportunities"],
                            "correct_answer": "Career advancement opportunities",
                            "points": 1,
                            "order_index": 3
                        },
                        {
                            "question_text": "Which skill do you consider your strongest?",
                            "options": ["Technical/analytical skills", "Communication skills", "Creative thinking", "Leadership and management"],
                            "correct_answer": "Technical/analytical skills",
                            "points": 1,
                            "order_index": 4
                        },
                        {
                            "question_text": "Your long-term career goal is:",
                            "options": ["Executive leadership", "Technical expertise", "Entrepreneurship", "Work-life balance"],
                            "correct_answer": "Technical expertise",
                            "points": 1,
                            "order_index": 5
                        }
                    ]
                },
                # Skills Questions
                {
                    "assessment_type": assessment_types[2],
                    "questions": [
                        {
                            "question_text": "How comfortable are you with learning new technologies?",
                            "options": ["Very uncomfortable", "Somewhat uncomfortable", "Neutral", "Comfortable", "Very comfortable"],
                            "correct_answer": "Comfortable",
                            "points": 1,
                            "order_index": 1
                        },
                        {
                            "question_text": "When working on projects, you prefer:",
                            "options": ["Working independently", "Collaborating with a small team", "Leading a team", "Following clear instructions"],
                            "correct_answer": "Collaborating with a small team",
                            "points": 1,
                            "order_index": 2
                        },
                        {
                            "question_text": "How do you handle tight deadlines?",
                            "options": ["Get stressed and anxious", "Work better under pressure", "Plan ahead to avoid last-minute work", "Delegate tasks to others"],
                            "correct_answer": "Plan ahead to avoid last-minute work",
                            "points": 1,
                            "order_index": 3
                        },
                        {
                            "question_text": "Your approach to problem-solving is:",
                            "options": ["Methodical and step-by-step", "Creative and out-of-the-box", "Collaborative and discussion-based", "Trial and error"],
                            "correct_answer": "Methodical and step-by-step",
                            "points": 1,
                            "order_index": 4
                        },
                        {
                            "question_text": "How important is continuous learning for your career?",
                            "options": ["Not important", "Somewhat important", "Important", "Very important", "Essential"],
                            "correct_answer": "Very important",
                            "points": 1,
                            "order_index": 5
                        }
                    ]
                }
            ]
            
            # Add all questions to database
            for category_data in questions_data:
                for q_data in category_data["questions"]:
                    question = EnhancedQuestion(
                        assessment_type_id=category_data["assessment_type"].id,
                        question_text=q_data["question_text"],
                        question_type="multiple_choice",
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        points=q_data["points"],
                        order_index=q_data["order_index"]
                    )
                    db.add(question)
            
            db.commit()
            print("Enhanced assessment data initialized successfully")
            
        except Exception as e:
            db.rollback()
            print(f"Error initializing assessment data: {str(e)}")
            raise
    
    @staticmethod
    def start_assessment_session(db: Session, user_id: int, assessment_type_id: int) -> EnhancedAssessmentSession:
        """Start a new assessment session"""
        try:
            session = EnhancedAssessmentSession(
                user_id=user_id,
                assessment_type_id=assessment_type_id,
                status="in_progress",
                started_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error starting assessment session: {str(e)}")
    
    @staticmethod
    def submit_assessment_responses(
        db: Session, 
        session_id: int, 
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Submit assessment responses and calculate scores"""
        try:
            session = db.query(EnhancedAssessmentSession).filter(
                EnhancedAssessmentSession.id == session_id
            ).first()
            
            if not session:
                return {"error": "Session not found"}
            
            total_score = 0
            max_score = 0
            
            for response_data in responses:
                question = db.query(EnhancedQuestion).filter(
                    EnhancedQuestion.id == response_data["question_id"]
                ).first()
                
                if question:
                    is_correct = response_data["user_answer"] == question.correct_answer
                    points_earned = question.points if is_correct else 0
                    
                    response = EnhancedAssessmentResponse(
                        session_id=session_id,
                        question_id=response_data["question_id"],
                        user_answer=response_data["user_answer"],
                        is_correct=is_correct,
                        points_earned=points_earned,
                        response_time_seconds=response_data.get("response_time_seconds", 0)
                    )
                    
                    db.add(response)
                    total_score += points_earned
                    max_score += question.points
            
            # Update session with scores
            session.total_score = total_score
            session.max_score = max_score
            session.percentage = (total_score / max_score * 100) if max_score > 0 else 0
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            
            # Calculate time taken
            if session.started_at:
                time_taken = (session.completed_at - session.started_at).total_seconds()
                session.time_taken_seconds = int(time_taken)
            
            db.commit()
            
            return {
                "session_id": session_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": session.percentage,
                "time_taken": session.time_taken_seconds
            }
            
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def generate_mock_video_analysis(session_id: int, recording_id: int) -> MockVideoAnalysis:
        """Generate comprehensive mock video analysis"""
        # Emotional analysis
        emotions = ["happiness", "sadness", "anger", "surprise", "fear", "disgust", "neutral"]
        emotional_analysis = {emotion: round(random.uniform(0.05, 0.35), 2) for emotion in emotions}
        
        # Normalize to sum to 1
        total = sum(emotional_analysis.values())
        for emotion in emotions:
            emotional_analysis[emotion] = round(emotional_analysis[emotion] / total, 2)
        
        dominant_emotion = max(emotional_analysis, key=emotional_analysis.get)
        
        # Career predictions
        career_categories = {
            "technology": ["Software Developer", "Data Scientist", "AI Engineer", "Cybersecurity Analyst"],
            "healthcare": ["Doctor", "Nurse", "Medical Researcher", "Psychologist"],
            "business": ["Business Analyst", "Marketing Manager", "Financial Advisor", "Entrepreneur"],
            "creative": ["Graphic Designer", "Content Creator", "Architect", "Film Director"]
        }
        
        recommended_careers = random.sample(
            career_categories[random.choice(list(career_categories.keys()))], 
            3
        )
        
        analysis = MockVideoAnalysis(
            session_id=session_id,
            video_recording_id=recording_id,
            emotional_analysis=emotional_analysis,
            mood_score=round(random.uniform(0.6, 0.9), 2),
            dominant_emotion=dominant_emotion,
            engagement_level=round(random.uniform(0.7, 0.95), 2),
            focus_score=round(random.uniform(0.65, 0.9), 2),
            confidence_level=round(random.uniform(0.6, 0.85), 2),
            motivation_level=round(random.uniform(0.7, 0.9), 2),
            personality_insights={
                "openness": round(random.uniform(0.6, 0.9), 2),
                "conscientiousness": round(random.uniform(0.5, 0.8), 2),
                "extraversion": round(random.uniform(0.4, 0.7), 2),
                "agreeableness": round(random.uniform(0.6, 0.8), 2),
                "neuroticism": round(random.uniform(0.2, 0.5), 2)
            },
            attention_metrics={
                "gaze_stability": round(random.uniform(0.7, 0.9), 2),
                "blink_rate": random.choice(["low", "normal", "slightly_high"]),
                "head_movement": random.choice(["minimal", "moderate", "active"]),
                "posture_consistency": round(random.uniform(0.6, 0.85), 2)
            },
            cognitive_analysis={
                "concentration_level": round(random.uniform(0.7, 0.9), 2),
                "mental_workload": random.choice(["low", "moderate", "high"]),
                "problem_solving_efficiency": round(random.uniform(0.6, 0.85), 2),
                "decision_making_speed": random.choice(["deliberate", "balanced", "quick"])
            },
            problem_solving_style=random.choice(["analytical", "creative", "practical", "theoretical"]),
            career_predictions={
                "recommended_careers": recommended_careers,
                "compatibility_scores": [round(random.uniform(0.7, 0.95), 2) for _ in range(3)],
                "key_strengths": random.sample(["Analytical Thinking", "Creativity", "Leadership", "Technical Skills", "Communication"], 3),
                "development_areas": random.sample(["Public Speaking", "Time Management", "Technical Depth", "Strategic Thinking"], 2)
            },
            overall_score=round(random.uniform(0.7, 0.9), 2),
            analysis_remarks="The candidate demonstrated strong engagement and positive emotional indicators throughout the assessment. Cognitive metrics suggest good problem-solving abilities and sustained focus. Career recommendations are based on behavioral patterns and response analysis.",
            processed_at=datetime.utcnow()
        )
        
        return analysis