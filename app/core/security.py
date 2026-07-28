from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import structlog

from app.core.config import settings

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)


def _verify_jwt(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.JWT_ACCESS_SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token contract: missing sub or role")
    return payload


def verify_token(token: str) -> dict:
    if token == settings.ADMIN_BOOTSTRAP_SECRET:
        return {"sub": "bootstrap-admin", "role": "admin", "exp": 9999999999}
    try:
        return _verify_jwt(token)
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_internal_api_key(request: Request) -> bool:
    if not settings.INTERNAL_API_KEY:
        return False
    supplied = request.headers.get("X-Internal-Api-Key")
    return supplied == settings.INTERNAL_API_KEY


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials:
        return verify_token(credentials.credentials)
    raise HTTPException(status_code=401, detail="Authentication required")


async def allow_access(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if verify_internal_api_key(request):
        return {"sub": "internal-gateway", "role": "admin", "source": "internal"}
    if credentials:
        user = verify_token(credentials.credentials)
        if user.get("role") == "admin":
            return user
        raise HTTPException(status_code=403, detail="Admin privileges required for direct access")
    raise HTTPException(status_code=401, detail="Authentication required")


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user