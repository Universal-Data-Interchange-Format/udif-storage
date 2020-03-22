"""
data_access/models/__init__.py

This class brings all of the models together (with a declarative base for sqlalchemy).
"""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .udif import Udif
from .api_key import ApiKey