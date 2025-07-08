"""Database interaction functions."""

from typing import Optional
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta

from models import (
    Base,
    ReportModel,
    StatusEnum,
    SentimentEnum,
    CategoryEnum,
)

engine = create_engine("sqlite:///database.db", echo=True)

SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """
    Creates tables in the database if they do not already exist.
    """
    Base.metadata.create_all(bind=engine)


def save_report(
    text: str,
    status: Optional[StatusEnum] = StatusEnum.open,
    sentiment: Optional[SentimentEnum] = SentimentEnum.unknown,
    category: Optional[CategoryEnum] = CategoryEnum.other,
) -> int:
    """
    Saves the complaint to the database.

    Args:
        text: The text of the complaint.
        status: The status of the complaint.
        sentiment: Emotional coloring.
        category: The complaint category.

    Returns:
        The ID of the created report.
    """
    session: Session = SessionLocal()
    try:
        report = ReportModel(
            text=text,
            status=status,
            sentiment=sentiment,
            category=category,
        )
        session.add(report)
        session.commit()
        session.refresh(report)
        return report.id
    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        session.close()


def update_report(
    report_id: int,
    status: Optional[StatusEnum] = None,
    sentiment: Optional[SentimentEnum] = None,
    category: Optional[CategoryEnum] = None,
) -> int:
    """
    Update fields of a report in the database.

    Args:
        report_id (int): ID of the report to update.
        status (Optional[StatusEnum]): New status of the report.
        sentiment (Optional[SentimentEnum]): New sentiment classification.
        category (Optional[CategoryEnum]): New category of the report.

    Returns:
        int: ID of the updated report.

    Raises:
        ValueError: If the report with the given ID does not exist.
        Exception: For other database-related issues.
    """
    session = SessionLocal()
    try:
        report_from_db = session.query(ReportModel).filter(ReportModel.id == report_id).first()
        if report_from_db is None:
            raise ValueError(f"Report with id {report_id} not found.")

        if status is not None:
            report_from_db.status = status
        if sentiment is not None:
            report_from_db.sentiment = sentiment
        if category is not None:
            report_from_db.category = category

        session.commit()
        session.refresh(report_from_db)
        return report_from_db.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_reports_from_db():
    """
    Retrieve reports from the database that were created within the last hour.

    Returns:
        List[ReportModel]: A list of report objects created within the past hour.

    Raises:
        Exception: For any database-related errors during the query.
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    session = SessionLocal()
    try:
        reports = (session
                   .query(ReportModel)
                   .filter(ReportModel.timestamp >= one_hour_ago and ReportModel.status == 'open')
                   .all()
                   )
        return reports
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
