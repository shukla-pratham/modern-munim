from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    MANAGER = "manager"  # B2B: Business managers


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(
        SQLEnum(
            UserRole,
            name="userrole",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        default=UserRole.CUSTOMER,
        nullable=False,
    )
    mfa_enabled = Column(Boolean, nullable=False, server_default="false", default=False)
    mfa_secret = Column(String, nullable=True)
    store_name = Column(String, nullable=True)
    store_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="user")
    workspace_memberships = relationship("WorkspaceMembership", back_populates="user", cascade="all, delete-orphan")

