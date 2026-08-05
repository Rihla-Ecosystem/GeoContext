from sqladmin import ModelView
from fastapi import Request

from app.models.site import Site
from app.models.boundary import Boundary
from app.models.restricted_zone import RestrictedZone
from app.models.location_warning import LocationWarning
from app.models.nearby_service import NearbyService
from app.models.audit_log import AuditLog

from app.core.security import verify_token

class AuditedModelView(ModelView):
    async def log_action(self, request: Request, action: str, model_instance, details: dict = None):

        token = request.session.get("token")

        admin_id = request.session.get("admin_id") or "unknown"
        if admin_id == "unknown":
            token = request.session.get("token")
            if token:
                try:
                    payload = verify_token(token)
                    admin_id = payload.get("sub", "unknown")
                except Exception:
                    pass

        target_id = str(getattr(model_instance, "id", "unknown"))
        target_type = model_instance.__tablename__

        log_entry = AuditLog(
            admin_identifier=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )

        self.session.add(log_entry)
        await self.session.flush()

    async def on_model_change(self, data: dict, model: object, is_created: bool, request: Request) -> None:
        action = "create" if is_created else "update"
        safe_data = {k: str(v) for k, v in data.items()}
        await self.log_action(request, action, model, details=safe_data)

    async def on_model_delete(self, model: object, request: Request) -> None:
        await self.log_action(request, "delete", model)

class SiteAdmin(AuditedModelView, model=Site):
    column_list = [Site.id, Site.name, Site.categories]
    column_searchable_list = [Site.name, Site.name_en]
    icon = "fa-solid fa-map-pin"

class BoundaryAdmin(AuditedModelView, model=Boundary):
    column_list = [Boundary.id, Boundary.name, Boundary.level]
    column_searchable_list = [Boundary.name, Boundary.name_en]
    icon = "fa-solid fa-border-all"

class RestrictedZoneAdmin(AuditedModelView, model=RestrictedZone):
    column_list = [RestrictedZone.id, RestrictedZone.name, RestrictedZone.subtype, RestrictedZone.source]
    icon = "fa-solid fa-ban"

class LocationWarningAdmin(AuditedModelView, model=LocationWarning):
    column_list = [LocationWarning.id, LocationWarning.title, LocationWarning.severity, LocationWarning.active, LocationWarning.location_id]
    column_searchable_list = [LocationWarning.title, LocationWarning.category]
    icon = "fa-solid fa-triangle-exclamation"
    can_create = True
    can_edit = True
    can_delete = True
    form_columns = ["location_id", "title", "description", "severity", "category", "active", "expires_at"]

class NearbyServiceAdmin(AuditedModelView, model=NearbyService):
    column_list = [NearbyService.id, NearbyService.name, NearbyService.type, NearbyService.distance_km, NearbyService.location_id]
    column_searchable_list = [NearbyService.name, NearbyService.type]
    icon = "fa-solid fa-location-dot"
    can_create = True
    can_edit = True
    can_delete = True
    form_columns = ["location_id", "name", "type", "distance_km", "lat", "lng", "rating", "contact"]

class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [AuditLog.id, AuditLog.target_type, AuditLog.action, AuditLog.admin_identifier, AuditLog.created_at]
    icon = "fa-solid fa-clipboard-list"
    can_create = False
    can_edit = False
    can_delete = False
