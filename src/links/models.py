import uuid
from datetime import datetime
from sqlalchemy import Column, String, TIMESTAMP, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_code = Column(String(50), unique=True, nullable=False, index=True)
    original_url = Column(String(2048), nullable=False)
    custom_alias = Column(String(50), unique=True, nullable=True, index=True)
    
    # User relationship - NULL for anonymous users
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=True)
    last_used_at = Column(TIMESTAMP, nullable=True)
    
    # Statistics
    click_count = Column(Integer, default=0, nullable=False)
    
    # Optional: categorization
    category = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_original_url', 'original_url'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )
