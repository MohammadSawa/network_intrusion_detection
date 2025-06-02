from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

# Create SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./anomaly_detection.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    traffic_logs = relationship("TrafficLog", back_populates="workspace", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Store hashed password
    api_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    traffic_logs = relationship("TrafficLog", back_populates="user", cascade="all, delete-orphan")

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_ip = Column(String)
    destination_ip = Column(String)
    protocol = Column(String)
    status = Column(String)
    headers = Column(JSON)
    payload_size = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="traffic_logs")
    workspace = relationship("Workspace", back_populates="traffic_logs")

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 