from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from .settings import Settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: int, secret: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, secret, algorithm="HS256")


def current_user_id(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> int:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, Settings.from_environment().auth_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", headers={"WWW-Authenticate": "Bearer"})
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", headers={"WWW-Authenticate": "Bearer"})
    return user_id