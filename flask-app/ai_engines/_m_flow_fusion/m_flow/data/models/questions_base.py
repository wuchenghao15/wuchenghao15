"""
Questions ORM Base Module
=========================

Provides the SQLAlchemy declarative base for question-related
database models used in evaluation and testing.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class QuestionsBase(DeclarativeBase):
    """
    SQLAlchemy declarative base for question tables.

    Inherit from this class when creating ORM models that
    store question data in the evaluation database.
    """

    pass
