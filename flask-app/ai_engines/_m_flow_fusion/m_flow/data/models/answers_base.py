"""
Answers ORM Base Module
=======================

Provides the SQLAlchemy declarative base for answer-related
database models in the evaluation framework.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class AnswersBase(DeclarativeBase):
    """
    SQLAlchemy declarative base for answer tables.

    Inherit from this class when creating ORM models that
    store answer data in the evaluation database.
    """

    pass
