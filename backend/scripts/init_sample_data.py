import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models.assessment_models import AssessmentType, Question

def init_sample_assessments():
    db = SessionLocal()
    try:
        # Create sample assessment types
        assessment_types = [
            AssessmentType(
                name="PHQ-9 Depression Scale",
                description="A 9-item depression scale to assess depressive symptoms",
                category="Psychology",
                duration_minutes=5,
                questions_count=9
            ),
            AssessmentType(
                name="WHO-5 Well-Being Index",
                description="A 5-item questionnaire measuring current mental well-being",
                category="Psychology",
                duration_minutes=3,
                questions_count=5
            ),
            AssessmentType(
                name="Career Interest Inventory",
                description="Assess your interests across different career fields",
                category="Career",
                duration_minutes=10,
                questions_count=15
            ),
            AssessmentType(
                name="Skills Aptitude Test",
                description="Evaluate your aptitude across various skill domains",
                category="Skills",
                duration_minutes=15,
                questions_count=20
            ),
            AssessmentType(
                name="Psychology Personality Test",
                description="Comprehensive personality assessment based on psychological models",
                category="Psychology",
                duration_minutes=12,
                questions_count=25
            )
        ]
        
        for assessment in assessment_types:
            if not db.query(AssessmentType).filter(AssessmentType.name == assessment.name).first():
                db.add(assessment)
        
        db.commit()
        
        # Create sample questions for Career Interest Inventory
        career_assessment = db.query(AssessmentType).filter(AssessmentType.name == "Career Interest Inventory").first()
        if career_assessment:
            career_questions = [
                Question(
                    assessment_type_id=career_assessment.id,
                    question_text="How much do you enjoy working with numbers and data analysis?",
                    question_type="likert_scale",
                    options=["Not at all", "Slightly", "Moderately", "Very much", "Extremely"],
                    order_index=1
                ),
                Question(
                    assessment_type_id=career_assessment.id,
                    question_text="Do you prefer working in teams or individually?",
                    question_type="multiple_choice",
                    options=["Strongly prefer individual work", "Prefer individual work", "No preference", "Prefer team work", "Strongly prefer team work"],
                    order_index=2
                ),
                Question(
                    assessment_type_id=career_assessment.id,
                    question_text="How comfortable are you with public speaking and presentations?",
                    question_type="likert_scale",
                    options=["Very uncomfortable", "Somewhat uncomfortable", "Neutral", "Comfortable", "Very comfortable"],
                    order_index=3
                ),
            ]
            
            for question in career_questions:
                if not db.query(Question).filter(
                    Question.assessment_type_id == question.assessment_type_id,
                    Question.question_text == question.question_text
                ).first():
                    db.add(question)
        
        db.commit()
        print("Sample assessment data initialized successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_sample_assessments()