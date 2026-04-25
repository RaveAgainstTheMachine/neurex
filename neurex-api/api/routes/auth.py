"""
api/routes/auth.py
User authentication and RBAC logic.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import User, UserRole, get_session

router = APIRouter()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "neurex-super-secret-key-007")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise credentials_exception
    return user

def require_role(role: UserRole):
    """Dependency factory for RBAC."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        # Admin can do anything
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Developer check
        if role == UserRole.DEVELOPER and current_user.role in [UserRole.ADMIN, UserRole.DEVELOPER]:
            return current_user
            
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return current_user
    return role_checker

@router.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    # Check if first user - make them admin
    result = await session.exec(select(User))
    users = result.all()
    role = UserRole.ADMIN if not users else UserRole.DEVELOPER
    
    user = User(
        username=form_data.username,
        hashed_password=hash_password(form_data.password),
        role=role
    )
    session.add(user)
    try:
        await session.commit()
    except:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return {"message": "User created", "role": role}

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "id": current_user.id
    }
