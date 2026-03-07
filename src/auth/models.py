from datetime import datetime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, TIMESTAMP
from src.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
