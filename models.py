from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'

	id = Column('users_id', Integer, primary_key=True)
	name = Column(String)
	email = Column(String, unique=True)
	games = relationship('Game', lazy='dynamic')

	def __repr__(self):
		return "<User('%s','%s')>" % (self.name, self.email)

class Game(Base):
	__tablename__ = 'games'

	id = Column(Integer, primary_key=True)
	name = Column(String, unique=True)
	user_id = Column(Integer, ForeignKey('users.users_id'), nullable=False, onupdate='CASCADE')
	user = relationship('User', backref='users')

	def __repr__(self):
		return "<Game('%s','%s')>" % (self.name)