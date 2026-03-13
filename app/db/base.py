"""
SQLAlchemy base and declarative model setup.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
