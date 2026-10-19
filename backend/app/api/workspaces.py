"""
API endpoints for Workspace management, workspace switching,
and onboarding progress tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_workspace, WorkspaceContext, get_current_admin
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership
from app.schemas.workspace import (
    WorkspaceResponse,
    WorkspaceSummaryResponse,
    WorkspaceCreate,
    OnboardingProgressUpdate,
    DeleteWorkspaceRequest,
)
from app.services.workspace_service import (
    is_founder_user,
    get_user_memberships,
    create_user_workspace,
)
from app.services.admin_auth_service import resend_otp
from app.core.security import verify_password
from app.models.email_otp import EmailOtp
from datetime import timezone, datetime

router = APIRouter()


@router.get("/current", response_model=WorkspaceResponse)
def get_active_workspace(
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """Return the currently active workspace context."""
    return WorkspaceResponse(
        id=ctx.workspace.id,
        name=ctx.workspace.name,
        slug=ctx.workspace.slug,
        store_type=ctx.workspace.store_type,
        is_demo=ctx.workspace.is_demo,
        onboarding_completed=ctx.workspace.onboarding_completed,
        onboarding_step=ctx.workspace.onboarding_step,
        role=ctx.membership.role,
        created_at=ctx.workspace.created_at,
    )


@router.get("/summary", response_model=WorkspaceSummaryResponse)
def get_workspace_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    List all workspaces for the authenticated user along with their active workspace.
    Unassigned users receive an empty list without 403 error.
    """
    memberships = get_user_memberships(db, current_user.id)
    workspaces_data = []
    active_ws = None

    for m in memberships:
        ws_resp = WorkspaceResponse(
            id=m.workspace.id,
            name=m.workspace.name,
            slug=m.workspace.slug,
            store_type=m.workspace.store_type,
            is_demo=m.workspace.is_demo,
            onboarding_completed=m.workspace.onboarding_completed,
            onboarding_step=m.workspace.onboarding_step,
            role=m.role,
            created_at=m.workspace.created_at,
        )
        workspaces_data.append(ws_resp)
        if active_ws is None:
            active_ws = ws_resp

    return WorkspaceSummaryResponse(
        active_workspace=active_ws,
        workspaces=workspaces_data,
        is_founder=is_founder_user(current_user),
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_store_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new store workspace for the authenticated user and assign them as owner.
    """
    workspace, membership = create_user_workspace(
        db,
        user=current_user,
        store_name=data.name.strip(),
        store_type=data.store_type.strip() if data.store_type else None,
        is_demo=False,
    )
    db.commit()
    db.refresh(workspace)
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        store_type=workspace.store_type,
        is_demo=workspace.is_demo,
        onboarding_completed=workspace.onboarding_completed,
        onboarding_step=workspace.onboarding_step,
        role=membership.role,
        created_at=workspace.created_at,
    )


@router.post("/{workspace_id}/request-delete-otp", status_code=status.HTTP_200_OK)
def request_store_delete_otp(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Send an OTP code to the store owner's email specifically to authorize store deletion.
    """
    user_memberships = get_user_memberships(db, current_user.id)
    if len(user_memberships) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your only store. You must have at least one store.",
        )

    target_membership = next((m for m in user_memberships if m.workspace_id == workspace_id), None)
    if not target_membership or target_membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the store owner can delete this store workspace.",
        )

    result = resend_otp(db, current_user.email)
    return {"message": "Verification OTP sent to your registered email.", "email": current_user.email}


@router.post("/{workspace_id}/delete", status_code=status.HTTP_200_OK)
def delete_store_workspace(
    workspace_id: int,
    body: DeleteWorkspaceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a store workspace and cascade its data.
    Requires password verification and OTP code verification.
    """
    # 1. Verify password
    if not current_user.password_hash or not verify_password(body.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect account password. Store deletion aborted.",
        )

    # 2. Verify OTP
    cleaned_otp = (body.otp or "").strip().replace(" ", "")
    if not cleaned_otp.isdigit() or len(cleaned_otp) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter the valid 6-digit verification code sent to your email.",
        )

    row = db.query(EmailOtp).filter(EmailOtp.email == current_user.email).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new verification code.",
        )

    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new code.",
        )

    if not verify_password(cleaned_otp, row.code_hash):
        row.attempt_count = int(row.attempt_count or 0) + 1
        db.add(row)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code. Please check your email.",
        )

    # 3. Verify user memberships & permissions
    user_memberships = get_user_memberships(db, current_user.id)
    if len(user_memberships) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your only store. You must have at least one store.",
        )

    target_membership = next((m for m in user_memberships if m.workspace_id == workspace_id), None)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store workspace not found.",
        )

    if target_membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the store owner can delete this store workspace.",
        )

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store workspace not found.",
        )

    # Clear OTP row on success
    db.delete(row)
    db.delete(workspace)
    db.commit()
    return {"message": f"Store '{workspace.name}' deleted successfully.", "deleted_id": workspace_id}


@router.put("/onboarding-progress", status_code=status.HTTP_200_OK)
def update_onboarding_progress(
    update_data: OnboardingProgressUpdate,
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Update onboarding completion and step for the current active workspace.
    """
    workspace = ctx.workspace
    if update_data.onboarding_completed is not None:
        workspace.onboarding_completed = update_data.onboarding_completed
    if update_data.onboarding_step is not None:
        workspace.onboarding_step = update_data.onboarding_step

    db.commit()
    db.refresh(workspace)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        store_type=workspace.store_type,
        is_demo=workspace.is_demo,
        onboarding_completed=workspace.onboarding_completed,
        onboarding_step=workspace.onboarding_step,
        role=ctx.membership.role,
        created_at=workspace.created_at,
    )


@router.post("/demo/seed")
def seed_demo_data(
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Seed deterministic demo data into founder workspace.
    Guarded strictly to the verified founder email.
    """
    from app.services.demo_seeder_service import seed_founder_demo_data
    return seed_founder_demo_data(db, user=ctx.user, workspace=ctx.workspace)


@router.post("/demo/reset")
def reset_demo_data(
    db: Session = Depends(get_db),
    ctx: WorkspaceContext = Depends(get_current_workspace)
):
    """
    Safely reset demo data from founder workspace.
    Guarded strictly to the verified founder email.
    """
    from app.services.demo_seeder_service import reset_founder_demo_data
    return reset_founder_demo_data(db, user=ctx.user, workspace=ctx.workspace)

