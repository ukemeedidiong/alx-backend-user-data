#!/usr/bin/env python3
"""DB module
"""
import logging
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.exc import NoResultFound

from user import Base, User

logging.disable(logging.WARNING)


class DB:
    """DB class for interacting with the SQLite database.
    """

    def __init__(self) -> None:
        """Initialize a new DB instance.
        """
        self._engine = create_engine("sqlite:///a.db", echo=True)
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)
        self.__session: Optional[Session] = None

    @property
    def _session(self) -> Session:
        """Memoized session object.
        """
        if self.__session is None:
            DBSession = sessionmaker(bind=self._engine)
            self.__session = DBSession()
        return self.__session

    def add_user(self, email: str, hashed_password: str) -> User:
        """Adds a new  to the database the given email and hashed password.

        Args:
            email (str): The email address of the new user.
            hashed_password (str): The hashed password of the new user.

        Returns:
            User: A User object representing the new user.
        """
        new_user = User(email=email, hashed_password=hashed_password)
        try:
            self._session.add(new_user)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise Exception(f"Error adding user to database: {e}")
        return new_user

    def find_user_by(self, **kwargs: Dict[str, str]) -> User:
        """Find a user by specified attributes.

        Args:
            **kwargs: Arbitrary arguments specifying the user's attributes.

        Raises:
            NoResultFound: When no results are found.
            InvalidRequestError: When invalid query arguments are passed.

        Returns:
            User: First row found in the `users` table.
        """
        try:
            user = self._session.query(User).filter_by(**kwargs).one()
        except NoResultFound:
            raise NoResultFound()
        except InvalidRequestError:
            raise InvalidRequestError()
        return user

    def update_user(self, user_id: int, **kwargs: Dict[str, str]) -> None:
        """Updates a user's attributes by ID and arbitrary keyword arguments.

        Args:
            user_id (int): The ID of the user to update.
            **kwargs: Keyword arguments representing the attributes to update.

        Raises:
            ValueError: If an invalid attribute kwargs or the is not found.

        Returns:
            None
        """
        try:
            user = self.find_user_by(id=user_id)
        except NoResultFound:
            raise ValueError(f"User with id {user_id} not found")

        for key, value in kwargs.items():
            if not hasattr(user, key):
                raise ValueError(f"User has no attribute {key}")
            setattr(user, key, value)

        try:
            self._session.commit()
        except InvalidRequestError:
            self._session.rollback()
            raise ValueError("Invalid request")


if __name__ == "__main__":
    db = DB()
    new_user = db.add_user("test@example.com", "hashed_password")
    print(new_user)
    found_user = db.find_user_by(email="test@example.com")
    print(found_user)
    db.update_user(new_user.id, email="new_email@example.com")
    updated_user = db.find_user_by(id=new_user.id)
    print(updated_user)
