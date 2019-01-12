from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

association_table = Table('association', Base.metadata,
						  Column('user_if', Integer, ForeignKey('User.id')),
						  Column('game_id', Integer, ForeignKey('Game.id'))
						  )

class User(Base):
	__tablename__ = 'User'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	email = Column(String, unique=True)
	games = relationship('Game',
						 secondary=association_table,
						 back_populates="user")

	def __repr__(self):
		return "<User('%s','%s')>" % (self.name, self.email)

class Game(Base):
	__tablename__ = 'Game'

	id = Column(Integer, primary_key=True)
	name = Column(String, unique=True)
	steam_id = Column(Integer, unique=True)
	user = relationship('User', secondary=association_table,
						back_populates="games")

	def __repr__(self):
		return "<Game('%s')>" % (self.name)
