
from . import Base
from sqlalchemy import Column, Integer, String

class ApiKey (Base):
    """
    This class represents the `udif` table in the database.

    Most notable is the `contents` column which contains the actual UDIF, however it is likely also worthwhile to store
    certain values from the UDIF file as indexed columns to improve access speed with a large amount of data.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String(32), unique=True, nullable=False)
    description = Column(String)
    contact_email = Column(String)

    def __repr__(self):
        return "<ApiKey(id={id}, key={key}, description={description})>".format(id=self.id, key=self.key, description=self.description)
