"""
postgres_udif_storage.py

This class contains methods for the storage and retrieval of UDIF files in a postgres database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_access.models import *

class PostgresUdifStorage:
    """
    The `PostgresUdifStorage` class contains methods for the storage and retrieval of UDIF files in a Postgres database.

    Overview
    --------

    TBD

    Example Usage
    -------------

    TBD
    """

    def __init__(self, connection_string : str):
        """
        Initialize a new PostgresUdifStorage instance with the given connection string.

        :param connection_string The connection string to use.
        """
        self.engine = create_engine(connection_string)
        self.session = sessionmaker(self.engine)
    
    def authenticate(self, api_key : str) -> bool:
        """
        Authenticate a client by confirming their API key is in the database.
        """
        return self.session().query(ApiKey) \
            .filter_by(key=api_key) \
            .first() is not None

    def create_all(self) -> None:
        """
        Create the tables specified in the sqlalchemy metadata.

        NOTE: It is expected that this method is not necessary to use in production.
        """

        Base.metadata.create_all(self.engine)

    def ensure_created(self) -> None:
        """
        Check that the required tables exist in the database; if they do not, throw an exception.
        """
        pass
    
    def create(self, udif : Udif) -> None:
        """
        Save a new record in the database.
        """
        session = self.session()
        obj = Udif(contents=udif)
        session.add(obj)
        session.commit()
    
    def create_or_update(self, udif : Udif) -> None:
        """
        Create a new record in the database if it does not exist, otherwise update an existing record.
        """
        
        match = self.find(id=udif.id, user_id=udif.user_id)
        if not match:
            self.create(udif)
        else:
            match.contents = udif.contents
            match.demographic_information = udif.demographic_information
    
    def update(self, udif : Udif) -> None:
        """
        Update a UDIF object.
        """
    
    def find(self, id : str = None, user_id : str = None) -> Udif:
        """
        Load a record out of the database based on the record's ID or user ID.

        Note that one of the keyword parameters must be specified.
        """
        
        if id is None and user_id is None:
            raise ValueError("kwargs `id` and `user_id` cannot both be None.")

        session = self.session()
        query = session.query(Udif)
        if id is not None:
            query = query.filter_by(id=id)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        
        return query.first()
