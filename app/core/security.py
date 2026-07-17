from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import structlog

from app.core.config import settings

logger = structlog.get_logger()
security = HTTPBearer()

def verify_token(token: str) -> dict:
    """
    Verifies the JWT token and extracts claims.
    Expected JWT contract claims: sub (user id), role (user/admin), exp (expiration).
    """
    # Bypass for explicit TODO-tagged tech debt (Admin bootstrap)
    if token == settings.ADMIN_BOOTSTRAP_SECRET:
        return {
            "sub": "bootstrap-admin",
            "role": "admin",
            "exp": 9999999999
        }

    try:
        # Standard HS256 verification using the Supabase shared secret
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        
        # Verify required claims contract
        if "sub" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token contract: missing sub or role")
            
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to inject the current user into standard endpoints."""
    return verify_token(credentials.credentials)

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency to restrict an endpoint to admins only."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
