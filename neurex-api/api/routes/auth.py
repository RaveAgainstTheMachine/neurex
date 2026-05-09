"""
api/routes/auth.py
User authentication and RBAC logic.
"""

import json
import os
import secrets
import time
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.task_graph import InviteCode, User, UserRole, get_session

log = structlog.get_logger()

router = APIRouter()


# Configuration
def get_secret_key() -> str:
    key = os.getenv("JWT_SECRET")
    if not key:
        if os.getenv("DEBUG") == "true":
            log.warning(
                "auth.using_insecure_dev_secret", hint="Set JWT_SECRET in .env for production"
            )
            return "neurex-insecure-dev-secret-007"
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. Neurex cannot start without a secure key."
        )
    return key


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        log.warning("ws.auth_invalid_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        log.warning("ws.auth_user_not_found", user=username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
                detail="Operation not permitted for your role",
            )
        return current_user

    return role_checker


class OnboardingManager:
    _instance = None

    def __init__(self):
        self.init_token: str | None = None
        self.expiry: float = 0
        self.is_completed: bool = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OnboardingManager()
        return cls._instance

    def generate_token(self):
        self.init_token = secrets.token_hex(16)
        self.expiry = time.time() + (15 * 60)  # 15 minutes
        log.warning(
            "admin.onboarding_required",
            message="NEUREX ADMIN ONBOARDING REQUIRED",
            init_token=self.init_token,
            expires_in="15 MINUTES",
        )
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
        "expiry": manager.expiry,
    }


@router.post("/onboarding/setup")
async def setup_admin(
    username: str, password: str, token: str, session: AsyncSession = Depends(get_session)
):
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
        force_password_change=False,  # Master sets their own permanent password
    )
    session.add(user)
    await session.commit()
    manager.init_token = None  # Clear token after use
    return {"message": "Master Identity Synthesized"}


@router.post("/register")
async def register(
    invite_code: str,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # Verify invite code
    stmt = select(InviteCode).where(
        InviteCode.code == invite_code,
        InviteCode.is_used.is_(False),
        InviteCode.expires_at > datetime.now(UTC),
    )
    result = await session.exec(stmt)
    invitation = result.first()

    if not invitation:
        raise HTTPException(status_code=403, detail="Invalid, used, or expired invite code")

    user = User(
        username=form_data.username,
        hashed_password=hash_password(form_data.password),
        role=invitation.role,
        force_password_change=False,
    )
    session.add(user)

    # Mark invite code as used
    invitation.is_used = True
    session.add(invitation)

    try:
        await session.commit()
    except Exception as e:
        log.error("auth.register_commit_failed", error=str(e))
        raise HTTPException(
            status_code=400, detail="Registration failed: username may already exist"
        )

    return {"message": f"Account created with role: {invitation.role}", "role": invitation.role}


@router.post("/invite/create", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def create_invite(
    role: UserRole = UserRole.DEVELOPER,
    expires_in_hours: int = 24,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    import secrets

    code = secrets.token_urlsafe(16)
    expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)

    invitation = InviteCode(
        code=code, role=role, expires_at=expires_at, created_by=current_user.username
    )
    session.add(invitation)
    await session.commit()

    return {"invite_code": code, "role": role, "expires_at": expires_at.isoformat()}


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)
):
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

    if not user or not user.otp_enabled:
        raise HTTPException(status_code=400, detail="Invalid request")

    # Try TOTP first
    authenticated = False
    if user.otp_secret:
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(code):
            authenticated = True

    # Try backup codes if not authenticated
    if not authenticated and user.otp_backup_codes:
        hashed_codes = json.loads(user.otp_backup_codes)
        for i, hashed in enumerate(hashed_codes):
            if verify_password(code.upper(), hashed):
                authenticated = True
                # Remove the used code
                hashed_codes.pop(i)
                user.otp_backup_codes = json.dumps(hashed_codes)
                session.add(user)
                await session.commit()
                break

    if not authenticated:
        raise HTTPException(status_code=401, detail="Invalid OTP or backup code")

    if user.force_password_change:
        return {"password_change_required": True, "username": user.username}

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


@router.post("/change-password")
async def change_password(
    username: str,
    old_password: str,
    new_password: str,
    session: AsyncSession = Depends(get_session),
):
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
async def setup_otp(
    current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    import base64
    import io

    import pyotp
    import qrcode

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
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {"secret": current_user.otp_secret, "qr_code": f"data:image/png;base64,{img_str}"}


@router.post("/verify-otp")
async def verify_otp(
    code: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    import secrets

    import pyotp

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="OTP not setup")

    totp = pyotp.TOTP(current_user.otp_secret)
    if totp.verify(code):
        current_user.otp_enabled = True

        # Generate 8 backup codes
        plain_codes = [secrets.token_hex(4).upper() for _ in range(8)]
        hashed_codes = [hash_password(c) for c in plain_codes]
        current_user.otp_backup_codes = json.dumps(hashed_codes)

        session.add(current_user)
        await session.commit()
        return {"status": "enabled", "backup_codes": plain_codes}
    else:
        raise HTTPException(status_code=400, detail="Invalid code")


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role, "id": current_user.id}


@router.get("/users", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def list_users(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User))
    users = result.all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def update_user_role(
    user_id: str, role: UserRole, session: AsyncSession = Depends(get_session)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    session.add(user)
    await session.commit()
    return {"status": "updated", "role": role}


@router.delete("/users/{user_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"status": "deleted"}
