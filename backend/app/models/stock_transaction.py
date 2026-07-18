from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    STOCK_IN = "in"
    STOCK_OUT = "out"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # Positive for stock_in, negative for stock_out
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    reason = Column(String)  # e.g., "Manual restock", "Sale", "Return"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="stock_transactions")
