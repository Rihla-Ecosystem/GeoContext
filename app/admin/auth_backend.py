from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
import structlog

from app.core.security import verify_token

logger = structlog.get_logger()

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        # Workaround: Use the 'password' field in the standard SQLAdmin login form to paste the JWT Token
        token = form.get("password")
        
        if not token:
            return False
            
        try:
            payload = verify_token(token)
            if payload.get("role") != "admin":
                logger.warning("Non-admin attempted to login to dashboard", sub=payload.get("sub"))
                return False
            
            # Store the token securely in the encrypted session cookie
            request.session.update({"token": token})
            return True
        except Exception as e:
            logger.error("Admin login failed", error=str(e))
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
            
        try:
            # Re-verify the token on every page load to respect expiration
            payload = verify_token(token)
            return payload.get("role") == "admin"
        except Exception:
            return False

# Uses a secret key to sign the session cookies
authentication_backend = AdminAuth(secret_key="geocontext-admin-super-secret-key-replace-in-prod")
