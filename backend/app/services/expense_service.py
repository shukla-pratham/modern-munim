from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.expense import Expense, ExpenseCategory, ExpenseType
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def get_expenses(
    db: Session,
    workspace_id: int,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    product_id: Optional[int] = None
) -> List[Expense]:
    """Get expenses scoped to workspace with optional filtering"""
    query = db.query(Expense).filter(Expense.workspace_id == workspace_id)
    
    if category:
        try:
            expense_category = ExpenseCategory(category)
            query = query.filter(Expense.category == expense_category)
        except ValueError:
            pass
    
    if product_id:
        query = query.filter(Expense.product_id == product_id)
    
    return query.order_by(Expense.created_at.desc()).offset(skip).limit(limit).all()


def get_expense(db: Session, expense_id: int, workspace_id: int) -> Expense:
    """Get a single expense by ID scoped to workspace"""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.workspace_id == workspace_id,
    ).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return expense


def create_expense(db: Session, expense_data: ExpenseCreate, workspace_id: int, is_demo: bool = False) -> Expense:
    """Create a new expense scoped to workspace"""
    from app.models.product import Product
    # Validate category
    try:
        category = ExpenseCategory(expense_data.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {[e.value for e in ExpenseCategory]}"
        )
    
    # Validate expense type
    try:
        expense_type = ExpenseType(expense_data.expense_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid expense_type. Must be one of: {[e.value for e in ExpenseType]}"
        )
    
    if expense_data.product_id:
        p = db.query(Product).filter(
            Product.id == expense_data.product_id,
            Product.workspace_id == workspace_id,
        ).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {expense_data.product_id} not found",
            )

    db_expense = Expense(
        category=category,
        description=expense_data.description,
        amount=expense_data.amount,
        expense_type=expense_type,
        product_id=expense_data.product_id,
        workspace_id=workspace_id,
        is_demo=is_demo,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate, workspace_id: int) -> Expense:
    """Update an existing expense scoped to workspace"""
    expense = get_expense(db, expense_id, workspace_id=workspace_id)
    
    update_data = expense_data.dict(exclude_unset=True) if hasattr(expense_data, "dict") else expense_data.model_dump(exclude_unset=True)
    update_data.pop("workspace_id", None)
    update_data.pop("is_demo", None)
    
    # Handle category enum
    if "category" in update_data:
        try:
            update_data["category"] = ExpenseCategory(update_data["category"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Handle expense_type enum
    if "expense_type" in update_data:
        try:
            update_data["expense_type"] = ExpenseType(update_data["expense_type"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid expense_type"
            )
    
    if update_data.get("product_id"):
        from app.models.product import Product
        p = db.query(Product).filter(
            Product.id == update_data["product_id"],
            Product.workspace_id == workspace_id,
        ).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {update_data['product_id']} not found",
            )

    for field, value in update_data.items():
        setattr(expense, field, value)
    
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int, workspace_id: int) -> None:
    """Delete an expense scoped to workspace"""
    expense = get_expense(db, expense_id, workspace_id=workspace_id)
    db.delete(expense)
    db.commit()

