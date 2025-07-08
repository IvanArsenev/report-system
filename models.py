"""Models and enums used in the application."""

import enum
from typing import Optional

from sqlalchemy import (
    Column,
    Enum,
    DateTime,
    Text,
    Integer,
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()


class StatusEnum(str, enum.Enum):
    """Status of the report."""
    open = "open"
    closed = "closed"


class SentimentEnum(str, enum.Enum):
    """Sentiment classification of the report."""
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    unknown = "unknown"


class CategoryEnum(str, enum.Enum):
    """Report category classification."""
    technical = "техническая"
    payment = "оплата"
    other = "другое"


class ReportModel(Base):
    """SQLAlchemy model for the report table."""
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.open, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sentiment = Column(Enum(SentimentEnum), default=SentimentEnum.unknown, nullable=False)
    category = Column(Enum(CategoryEnum), default=CategoryEnum.other, nullable=False)


class ReportBody(BaseModel):
    """Pydantic model for incoming report data."""
    text: str
    status: Optional[StatusEnum] = StatusEnum.open


class ChangeStatusBody(BaseModel):
    """Pydantic model for incoming changes of report data."""
    report_id: int
    status: StatusEnum
