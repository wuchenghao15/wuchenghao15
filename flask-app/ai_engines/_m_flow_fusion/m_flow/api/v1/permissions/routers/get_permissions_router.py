"""
Permissions Router

REST API endpoints for managing access control in M-flow.
Handles dataset permissions, role management, and multi-tenancy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import Field

from m_flow.api.DTO import InDTO

if TYPE_CHECKING:
    from m_flow.auth.models import User


# ---------------------------------------------------------------------------
# Request DTOs
# ---------------------------------------------------------------------------


class TenantSelectionDTO(InDTO):
    """Payload for tenant selection request."""

    tenant_id: UUID | None = Field(default=None, description="Target tenant UUID or None for default")


# ---------------------------------------------------------------------------
# Telemetry Helper
# ---------------------------------------------------------------------------


def _emit_perm_event(user_id: UUID, endpoint: str, **extra) -> None:
    """Send telemetry for permissions API calls."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Permissions API Endpoint Invoked",
        user_id,
        additional_properties={"endpoint": endpoint, "m_flow_version": ver, **extra},
    )


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------


def _auth():
    """Return authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Response Helpers
# ---------------------------------------------------------------------------


def _ok(msg: str, **extra) -> JSONResponse:
    """Return a 200 JSON response with message and optional fields."""
    return JSONResponse(status_code=200, content={"message": msg, **extra})


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_permissions_router() -> APIRouter:
    """
    Build permissions management router.

    Endpoints:
        POST /datasets/{principal_id} - Grant dataset permissions
        POST /roles                   - Create a role
        POST /users/{user_id}/roles   - Assign user to role
        POST /users/{user_id}/tenants - Assign user to tenant
        POST /tenants                 - Create tenant
        POST /tenants/select          - Switch active tenant
    """
    router = APIRouter()

    # -----------------------------------------------------------------------
    # Dataset Permission Grant
    # -----------------------------------------------------------------------

    @router.post("/datasets/{principal_id}")
    async def grant_dataset_access(
        permission_name: str,
        dataset_ids: list[UUID],
        principal_id: UUID,
        user: "User" = Depends(_auth()),
    ):
        """
        Grant permission on datasets to a principal.

        Allows assigning read/write/delete/share permissions
        on specified datasets to a user or role.
        """
        _emit_perm_event(
            user.id,
            f"POST /v1/permissions/datasets/{principal_id}",
            dataset_ids=str(dataset_ids),
            principal_id=str(principal_id),
        )

        from m_flow.auth.permissions.methods import authorized_give_permission_on_datasets

        await authorized_give_permission_on_datasets(
            principal_id,
            list(dataset_ids),
            permission_name,
            user.id,
        )
        return _ok("Permission assigned to principal")

    # -----------------------------------------------------------------------
    # Role Management
    # -----------------------------------------------------------------------

    @router.post("/roles")
    async def create_new_role(
        role_name: str,
        user: "User" = Depends(_auth()),
    ):
        """
        Create a new access control role.

        Roles group permissions for easier user management.
        The authenticated user becomes the role owner.
        """
        _emit_perm_event(user.id, "POST /v1/permissions/roles", role_name=role_name)

        from m_flow.auth.roles.methods import create_role

        role_id = await create_role(role_name=role_name, owner_id=user.id)
        return _ok("Role created for tenant", role_id=str(role_id))

    @router.post("/users/{user_id}/roles")
    async def assign_role_to_user(
        user_id: UUID,
        role_id: UUID,
        user: "User" = Depends(_auth()),
    ):
        """
        Assign a user to an existing role.

        Grants the user all permissions associated with the role.
        Caller must be role owner or admin.
        """
        _emit_perm_event(
            user.id,
            f"POST /v1/permissions/users/{user_id}/roles",
            user_id=str(user_id),
            role_id=str(role_id),
        )

        from m_flow.auth.roles.methods import add_user_to_role

        await add_user_to_role(user_id=user_id, role_id=role_id, owner_id=user.id)
        return _ok("User added to role")

    # -----------------------------------------------------------------------
    # Tenant Management
    # -----------------------------------------------------------------------

    @router.post("/tenants")
    async def create_new_tenant(
        tenant_name: str,
        user: "User" = Depends(_auth()),
    ):
        """
        Create a new tenant for multi-tenant isolation.

        Tenants provide resource separation between
        different organizations or user groups.
        """
        _emit_perm_event(user.id, "POST /v1/permissions/tenants", tenant_name=tenant_name)

        from m_flow.auth.tenants.methods import create_tenant

        tenant_id = await create_tenant(tenant_name=tenant_name, user_id=user.id)
        return _ok("Tenant created.", tenant_id=str(tenant_id))

    @router.post("/users/{user_id}/tenants")
    async def assign_tenant_to_user(
        user_id: UUID,
        tenant_id: UUID,
        user: "User" = Depends(_auth()),
    ):
        """
        Add a user to an existing tenant.

        Enables the user to access tenant resources.
        Caller must be tenant owner or admin.
        """
        _emit_perm_event(
            user.id,
            f"POST /v1/permissions/users/{user_id}/tenants",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
        )

        from m_flow.auth.tenants.methods import add_user_to_tenant

        await add_user_to_tenant(user_id=user_id, tenant_id=tenant_id, owner_id=user.id)
        return _ok("User added to tenant")

    @router.post("/tenants/select")
    async def switch_active_tenant(
        payload: TenantSelectionDTO,
        user: "User" = Depends(_auth()),
    ):
        """
        Switch the user's active tenant context.

        Pass None to revert to the default single-user tenant.
        """
        _emit_perm_event(
            user.id,
            f"POST /v1/permissions/tenants/{payload.tenant_id}",
            tenant_id=str(payload.tenant_id),
        )

        from m_flow.auth.tenants.methods import select_tenant

        await select_tenant(user_id=user.id, tenant_id=payload.tenant_id)
        return _ok("Tenant selected.", tenant_id=str(payload.tenant_id))

    return router
