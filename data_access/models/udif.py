
from . import Base
from sqlalchemy import Column, Integer, String, cast
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

class CastingArray (ARRAY):
    def bind_expression(self, bindvalue):
        return cast(bindvalue, self)

class Udif (Base):
    """
    This class represents the `udif` table in the database.

    Most notable is the `contents` column which contains the actual UDIF, however it is likely also worthwhile to store
    certain values from the UDIF file as indexed columns to improve access speed with a large amount of data.
    """

    __tablename__ = "udif"

    id = Column(Integer, primary_key = True)
    user_id = Column(String, unique=True, nullable=False)
    demographic_information = Column(String)
    contents = Column(CastingArray(JSONB))

    def __repr__(self):
        return "<Udif(id={id}, user_id={user_id})>".format(id=self.id, user_id=self.user_id)
