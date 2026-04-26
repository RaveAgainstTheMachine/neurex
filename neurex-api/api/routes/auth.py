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
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
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

import time
import secrets
from typing import Optional, Dict

class OnboardingManager:
    _instance = None
    
    def __init__(self):
        self.init_token: Optional[str] = None
        self.expiry: float = 0
        self.is_completed: bool = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OnboardingManager()
        return cls._instance

    def generate_token(self):
        self.init_token = secrets.token_hex(16)
        self.expiry = time.time() + (15 * 60) # 15 minutes
        print("\n" + "="*60)
        print(" NEUREX ADMIN ONBOARDING REQUIRED ".center(60, "⬡"))
        print("="*60)
        print(f" INITIALIZATION TOKEN: {self.init_token}")
        print(f" EXPIRES IN: 15 MINUTES")
        print("="*60 + "\n")
        return self.init_token

    def verify_token(self, token: str) -> bool:
        if not self.init_token or time.time() > self.expiry:
            return False
        return secrets.compare_digest(self.init_token, token)

@router.get("/onboarding/status")
async def get_onboarding_status(session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.role == UserRole.ADMIN)
    result = await session.exec(statement)
    has_admin = result.first() is not None
    
    manager = OnboardingManager.get_instance()
    
    if not has_admin and not manager.init_token:
        manager.generate_token()
        
    return {
        "onboarding_required": not has_admin,
        "token_expired": time.time() > manager.expiry if manager.init_token else False,
        "expiry": manager.expiry
    }

@router.post("/onboarding/setup")
async def setup_admin(username: str, password: str, token: str, session: AsyncSession = Depends(get_session)):
    manager = OnboardingManager.get_instance()
    
    # Check if admin already exists
    statement = select(User).where(User.role == UserRole.ADMIN)
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    if not manager.verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired initialization token")
    
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
        force_password_change=False # Master sets their own permanent password
    )
    session.add(user)
    await session.commit()
    manager.init_token = None # Clear token after use
    return {"message": "Master Identity Synthesized"}

@router.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = User(
        username=form_data.username,
        hashed_password=hash_password(form_data.password),
        role=UserRole.DEVELOPER,
        force_password_change=False # User is setting their own password
    )
    session.add(user)
    try:
        await session.commit()
    except:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    return {"message": "Developer account created", "role": UserRole.DEVELOPER, "force_password_change": True}

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
    
    if user.force_password_change:
        return {"password_change_required": True, "username": user.username}

    if user.otp_enabled:
        return {"otp_required": True, "username": user.username}
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.post("/token-otp")
async def login_otp(username: str, code: str, session: AsyncSession = Depends(get_session)):
    import pyotp
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    
    if not user or not user.otp_enabled or not user.otp_secret:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")
    
    if user.force_password_change:
        return {"password_change_required": True, "username": user.username}

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.post("/change-password")
async def change_password(username: str, old_password: str, new_password: str, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    
    if not user or not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user.hashed_password = hash_password(new_password)
    user.force_password_change = False
    session.add(user)
    await session.commit()
    
    # Generate token after change
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.get("/setup-otp")
async def setup_otp(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    import pyotp
    import qrcode
    import io
    import base64
    
    if current_user.otp_enabled:
        return {"message": "OTP already enabled"}
    
    if not current_user.otp_secret:
        current_user.otp_secret = pyotp.random_base32()
        session.add(current_user)
        await session.commit()
    
    totp = pyotp.TOTP(current_user.otp_secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.username, issuer_name="Neurex")
    
    img = qrcode.make(provisioning_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "secret": current_user.otp_secret,
        "qr_code": f"data:image/png;base64,{img_str}"
    }

@router.post("/verify-otp")
async def verify_otp(code: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    import pyotp
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="OTP not setup")
    
    totp = pyotp.TOTP(current_user.otp_secret)
    if totp.verify(code):
        current_user.otp_enabled = True
        session.add(current_user)
        await session.commit()
        return {"status": "enabled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid code")

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "id": current_user.id
    }

@router.get("/users", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def list_users(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User))
    users = result.all()
    return [{ "id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active, "created_at": u.created_at } for u in users]

@router.patch("/users/{user_id}/role", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_user_role(user_id: str, role: UserRole, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    session.add(user)
    await session.commit()
    return {"status": "updated", "role": role}

@router.delete("/users/{user_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_user(user_id: str, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"status": "deleted"}
