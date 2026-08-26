from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Request
from passlib.context import CryptContext

from .settings import Settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


class AuthRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, action: str, maximum: int, window_seconds: int) -> bool:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            attempts = self._attempts[(key, action)]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= maximum:
                return False
            attempts.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


auth_rate_limiter = AuthRateLimiter()


def enforce_auth_rate_limit(request: Request, action: str, maximum: int, window_seconds: int) -> None:
    client_host = request.client.host if request.client else "unknown"
    if not auth_rate_limiter.allow(client_host, action, maximum, window_seconds):
        raise HTTPException(status_code=429, detail="Too many authentication attempts", headers={"Retry-After": str(window_seconds)})


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