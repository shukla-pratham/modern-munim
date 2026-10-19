from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_token_from_request(request: Request) -> str | None:
    if settings.JWT_COOKIE_NAME and settings.JWT_COOKIE_NAME in request.cookies:
        return request.cookies.get(settings.JWT_COOKIE_NAME)
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token (cookie or Bearer header)."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # MFA challenge tokens must not unlock authenticated APIs.
    if payload.get("mfa_pending"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    try:
        user_id: int = int(user_id_str)  # Convert string back to int for database query
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is an admin (role from server-side identity only)."""
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


class WorkspaceContext:
    def __init__(self, user: User, workspace, membership):
        self.user = user
        self.workspace = workspace
        self.membership = membership

    @property
    def workspace_id(self) -> int:
        return self.workspace.id

    @property
    def is_founder(self) -> bool:
        from app.services.workspace_service import is_founder_user
        return is_founder_user(self.user)

    @property
    def is_demo(self) -> bool:
        return bool(self.workspace.is_demo)


def get_current_workspace(
    request: Request,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> WorkspaceContext:
    """
    Ensure the caller has an active authorized workspace.
    Legacy users without store_name/workspaces are rejected with 403.
    Explicit X-Workspace-Id header is checked for membership to prevent IDOR.
    """
    from app.services.workspace_service import (
        ensure_user_workspace,
        get_user_memberships,
    )
    from app.models.workspace import WorkspaceMembership

    requested_wid = request.headers.get("X-Workspace-Id")
    if requested_wid and requested_wid.isdigit():
        wid = int(requested_wid)
        membership = (
            db.query(WorkspaceMembership)
            .filter(
                WorkspaceMembership.workspace_id == wid,
                WorkspaceMembership.user_id == current_user.id,
                WorkspaceMembership.is_active == True,
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access the requested workspace",
            )
        return WorkspaceContext(current_user, membership.workspace, membership)

    workspace, membership = ensure_user_workspace(db, current_user)
    if not workspace or not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace unassigned or store setup required. Please contact operator.",
        )
    return WorkspaceContext(current_user, workspace, membership)

