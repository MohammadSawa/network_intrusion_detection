from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr
import secrets
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from .database import get_db, User


pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256", "sha256_crypt"], deprecated="auto")


users: Dict[str, dict] = {}


api_key_header = APIKeyHeader(name="X-API-Key")

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(UserBase):
    id: int
    api_key: str

    class Config:
        from_attributes = True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    
    return pwd_context.hash(password)

def generate_api_key() -> str:
    
    return secrets.token_urlsafe(32)

async def get_user_by_api_key(db: Session, api_key: str) -> UserInDB:
    
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return UserInDB.model_validate(user)

def create_user(db: Session, username: str, email: str, password: str) -> UserInDB:
    
    try:
        
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        api_key = generate_api_key()
        hashed_password = get_password_hash(password)
        
        db_user = User(
            username=username,
            email=email,
            password=hashed_password,
            api_key=api_key
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserInDB.model_validate(db_user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

def authenticate_user(db: Session, username: str, password: str) -> UserInDB:
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return UserInDB.model_validate(user) 