from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    store_type: Optional[str] = None
    is_demo: bool = False
    onboarding_completed: bool = False
    onboarding_step: str = "store_profile"
    role: str = "owner"
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceSwitchRequest(BaseModel):
    workspace_id: int


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    store_type: Optional[str] = Field(None, max_length=50)



class OnboardingProgressUpdate(BaseModel):
    onboarding_completed: Optional[bool] = None
    onboarding_step: Optional[str] = None


class DeleteWorkspaceRequest(BaseModel):
    password: str
    otp: str


class WorkspaceSummaryResponse(BaseModel):
    active_workspace: Optional[WorkspaceResponse] = None
    workspaces: List[WorkspaceResponse] = []
    is_founder: bool = False
