from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_workspace, WorkspaceContext
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.services.expense_service import (
    get_expenses, get_expense, create_expense, update_expense, delete_expense
)

router = APIRouter()


@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Get list of expenses scoped to workspace."""
    expenses = get_expenses(
        db,
        workspace_id=workspace.workspace_id,
        skip=skip,
        limit=limit,
        category=category,
        product_id=product_id,
    )
    
    return [
        ExpenseResponse(
            id=exp.id,
            category=exp.category.value,
            description=exp.description,
            amount=exp.amount,
            expense_type=exp.expense_type.value,
            product_id=exp.product_id,
            product_name=exp.product.name if exp.product else None,
            created_at=exp.created_at
        )
        for exp in expenses
    ]


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_new_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Create a new expense scoped to workspace."""
    expense = create_expense(
        db,
        expense_data,
        workspace_id=workspace.workspace_id,
        is_demo=workspace.is_demo,
    )
    
    return ExpenseResponse(
        id=expense.id,
        category=expense.category.value,
        description=expense.description,
        amount=expense.amount,
        expense_type=expense.expense_type.value,
        product_id=expense.product_id,
        product_name=expense.product.name if expense.product else None,
        created_at=expense.created_at
    )


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense_by_id(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Update an expense scoped to workspace."""
    expense = update_expense(
        db,
        expense_id,
        expense_data,
        workspace_id=workspace.workspace_id,
    )
    
    return ExpenseResponse(
        id=expense.id,
        category=expense.category.value,
        description=expense.description,
        amount=expense.amount,
        expense_type=expense.expense_type.value,
        product_id=expense.product_id,
        product_name=expense.product.name if expense.product else None,
        created_at=expense.created_at
    )


@router.delete("/{expense_id}", status_code=204)
def delete_expense_by_id(
    expense_id: int,
    db: Session = Depends(get_db),
    workspace: WorkspaceContext = Depends(get_current_workspace),
):
    """Delete an expense scoped to workspace."""
    delete_expense(db, expense_id, workspace_id=workspace.workspace_id)
    return None

