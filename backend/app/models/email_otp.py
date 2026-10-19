from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class EmailOtp(Base):
    __tablename__ = "email_otps"

    email = Column(String, primary_key=True, nullable=False)
    code_hash = Column(String, nullable=False)
    store_name = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
