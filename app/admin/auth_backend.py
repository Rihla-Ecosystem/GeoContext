from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
import httpx
import structlog

from app.core.config import settings
from app.core.security import verify_token

logger = structlog.get_logger()

class AdminAuth(AuthenticationBackend):
    async def _verify_against_core(self, email: str, password: str):
        """Validate app-admin credentials directly against Core-Server's user store."""
        url = f"{settings.CORE_SERVER_URL.rstrip('/')}/api/internal/verify-admin-login"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    url,
                    json={"email": email, "password": password},
                    headers={"X-Internal-Api-Key": settings.INTERNAL_API_KEY},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning("Core admin verification failed", url=url, error=str(e))
        return {"ok": False}

    async def login(self, request: Request) -> bool:
        form = await request.form()
        # SQLAdmin's login form posts username + password
        username = (form.get("username") or form.get("email") or "").strip()
        password = form.get("password") or ""

        # 1. App-admin account from Core-Server (email + password, role must be "admin")
        core_result = await self._verify_against_core(username, password)
        if core_result.get("ok"):
            request.session.update({
                "admin_id": core_result.get("userId") or username,
                "admin_role": "admin",
            })
            return True

        # 2. Configured dashboard credentials
        if (
            settings.ADMIN_USERNAME
            and settings.ADMIN_PASSWORD
            and username == settings.ADMIN_USERNAME
            and password == settings.ADMIN_PASSWORD
        ):
            request.session.update({
                "admin_id": username,
                "admin_role": "admin",
            })
            return True

        # 3. Bootstrap secret (dev bypass)
        if password and password == settings.ADMIN_BOOTSTRAP_SECRET:
            request.session.update({
                "admin_id": "bootstrap-admin",
                "admin_role": "admin",
            })
            return True

        # 4. Admin JWT pasted into the password field (legacy)
        try:
            payload = verify_token(password)
            if payload.get("role") == "admin":
                request.session.update({
                    "admin_id": payload.get("sub", "jwt-admin"),
                    "admin_role": "admin",
                })
                return True
        except Exception as e:
            logger.warning("JWT admin login failed", error=str(e))

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if request.session.get("admin_role") == "admin":
            return True

        # Legacy sessions created by pasting an admin JWT
        token = request.session.get("token")
        if not token:
            return False
        try:
            payload = verify_token(token)
            return payload.get("role") == "admin"
        except Exception:
            return False

# Uses a secret key to sign the session cookies
authentication_backend = AdminAuth(secret_key="geocontext-admin-super-secret-key-replace-in-prod")
