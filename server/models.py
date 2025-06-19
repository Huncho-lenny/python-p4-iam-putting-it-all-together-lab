from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt

from config import db

bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    _password_hash = Column(String, nullable=False)
    image_url = Column(String)
    bio = Column(String)

    recipes = relationship("Recipe", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, '_password_hash') or self._password_hash is None:
            self.password_hash = "default123"

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, key, username):
        if not username or len(username.strip()) == 0:
            raise ValueError("Username must be present and non-empty.")
        return username


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    instructions = Column(String, nullable=False)
    minutes_to_complete = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="recipes")

    serialize_rules = ("-user.recipes",)

    @validates("instructions")
    def validate_instructions(self, key, instructions):
        if len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return instructions

