from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.expense import Expense, ExpenseCategory, ExpenseType
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def get_expenses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    product_id: Optional[int] = None
) -> List[Expense]:
    """Get expenses with optional filtering"""
    query = db.query(Expense)
    
    if category:
        try:
            expense_category = ExpenseCategory(category)
            query = query.filter(Expense.category == expense_category)
        except ValueError:
            pass
    
    if product_id:
        query = query.filter(Expense.product_id == product_id)
    
    return query.order_by(Expense.created_at.desc()).offset(skip).limit(limit).all()


def get_expense(db: Session, expense_id: int) -> Expense:
    """Get a single expense by ID"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    return expense


def create_expense(db: Session, expense_data: ExpenseCreate) -> Expense:
    """Create a new expense"""
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
    
    db_expense = Expense(
        category=category,
        description=expense_data.description,
        amount=expense_data.amount,
        expense_type=expense_type,
        product_id=expense_data.product_id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate) -> Expense:
    """Update an existing expense"""
    expense = get_expense(db, expense_id)
    
    update_data = expense_data.dict(exclude_unset=True)
    
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
    
    for field, value in update_data.items():
        setattr(expense, field, value)
    
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> None:
    """Delete an expense"""
    expense = get_expense(db, expense_id)
    db.delete(expense)
    db.commit()
