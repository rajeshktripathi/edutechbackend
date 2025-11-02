from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine
from app.models.base import Base
from app.models.user_models import Client, User, UserProfile
from app.models.assessment_models import AssessmentType, Question

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create default clients
    db = SessionLocal()
    try:
        default_clients = [
            Client(id=1, name="Default Corporate", description="Default corporate client"),
            Client(id=2, name="Client A", description="Corporate Client A"),
            Client(id=3, name="Client B", description="Corporate Client B"),
        ]
        
        for client in default_clients:
            if not db.query(Client).filter(Client.id == client.id).first():
                db.add(client)
        
        db.commit()
        print("Database initialized with default clients")
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()