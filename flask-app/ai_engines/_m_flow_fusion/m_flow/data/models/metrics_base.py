"""
Metrics ORM Base Module
=======================

Provides the SQLAlchemy declarative base for metrics-related
database models used in evaluation and analytics.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class MetricsBase(DeclarativeBase):
    """
    SQLAlchemy declarative base for metrics tables.

    Inherit from this class when creating ORM models that
    store metrics and evaluation data.
    """

    pass
