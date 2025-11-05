from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Base, Client

SQLALCHEMY_DATABASE_URL = "sqlite:///./careerpath.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
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