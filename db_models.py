from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=False)

    words = relationship('UserWord', back_populates='user')

class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True)
    target_word = Column(String, nullable=False)
    translate_word = Column(String, nullable=False)

    user_words = relationship('UserWord', back_populates='word')

class UserWord(Base):
    __tablename__ = 'user_words'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)

    user = relationship('User', back_populates='words')
    word = relationship('Word', back_populates='user_words')