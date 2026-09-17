"""Declarative ORM base shared by every M-Flow relational model.

All persistent SQLAlchemy models in the M-Flow stack must descend from
:class:`Base` so that Alembic migrations, async session loading, and
metadata introspection work consistently across the application.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Unified declarative root with first-class async attribute access.

    Combines SQLAlchemy's :class:`~sqlalchemy.orm.DeclarativeBase`
    with :class:`~sqlalchemy.ext.asyncio.AsyncAttrs` so that lazy-loaded
    relationships can be awaited transparently inside ``async with
    session`` blocks.
    """

    __abstract__ = True
