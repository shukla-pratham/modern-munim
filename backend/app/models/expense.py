from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ExpenseCategory(str, enum.Enum):
    INVENTORY = "inventory"
    OPERATIONS = "operations"
    MARKETING = "marketing"


class ExpenseType(str, enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(SQLEnum(ExpenseCategory), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    expense_type = Column(SQLEnum(ExpenseType), default=ExpenseType.ONE_TIME, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Nullable for global expenses
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="expenses")
