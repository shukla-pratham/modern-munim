import re
import unicodedata
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership

FOUNDER_EMAIL = "shuklapratham758@gmail.com"


def is_founder_user(user: User) -> bool:
    """Server-side check against authenticated User identity record."""
    if not user or not user.email:
        return False
    return user.email.strip().lower() == FOUNDER_EMAIL


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text) or "workspace"


def get_unique_slug(db: Session, base_name: str) -> str:
    base_slug = slugify(base_name)
    slug = base_slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first() is not None:
        counter += 1
        slug = f"{base_slug}-{counter}"
    return slug


def get_user_memberships(db: Session, user_id: int) -> list[WorkspaceMembership]:
    return (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.user_id == user_id, WorkspaceMembership.is_active == True)
        .all()
    )


def get_primary_membership(db: Session, user_id: int) -> WorkspaceMembership | None:
    return (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.user_id == user_id, WorkspaceMembership.is_active == True)
        .order_by(WorkspaceMembership.id.asc())
        .first()
    )


def create_user_workspace(
    db: Session,
    user: User,
    store_name: str,
    store_type: str | None = None,
    is_demo: bool = False,
) -> tuple[Workspace, WorkspaceMembership]:
    """Create a new workspace and assign the user as owner."""
    slug = get_unique_slug(db, store_name)
    workspace = Workspace(
        name=store_name,
        slug=slug,
        store_type=store_type,
        is_demo=is_demo,
        onboarding_completed=False,
        onboarding_step="store_profile",
    )
    db.add(workspace)
    db.flush()

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
        is_active=True,
    )
    db.add(membership)
    db.flush()
    return workspace, membership


def ensure_user_workspace(
    db: Session,
    user: User,
) -> tuple[Workspace, WorkspaceMembership] | tuple[None, None]:
    """
    Ensure a workspace exists for the user.
    If the user already has memberships, return the active primary.
    If the user has a store_name configured, create their workspace.
    For unassigned legacy users (with null store_name), do NOT guess; return None.
    """
    membership = get_primary_membership(db, user.id)
    if membership:
        return membership.workspace, membership

    if not user.store_name:
        return None, None

    is_demo = is_founder_user(user)
    workspace, membership = create_user_workspace(
        db,
        user=user,
        store_name=user.store_name,
        store_type=user.store_type,
        is_demo=is_demo,
    )
    db.commit()
    db.refresh(workspace)
    db.refresh(membership)
    return workspace, membership
