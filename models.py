from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()

attendees = Table('attendees', Base.metadata,
		Column('user', Integer, ForeignKey('users.id'), primary_key=True),
		Column('dinner', Integer, ForeignKey('dinners.id'), primary_key=True)
		)


class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	email = Column(String)
	password = Column(String)
	group = Column(Integer, ForeignKey('groups.id'))

	def __init__(self, name, email, password, group = None):
		self.name = name
		self.email = email
		self.password = self.hashPassword(password)
		self.group = group
	
	def __repr__(self):
		return "<User %i : %s>" % (self.id, self.name)

	def checkPassword(self, password):
		return self.hashPassword(password) == self.password

	def hashPassword(self, password):
		return hashlib.sha256(password + self.name + "sausage" ).hexdigest()


class Group(Base):
	__tablename__ = 'groups'

	id = Column(Integer, primary_key=True)
	code = Column(String)
	users = relationship("User", backref="g")
	dinners = relationship("Dinner", backref="g")

	def __repr__(self):
		return "<Group %i : %s>" % (self.id, str(self.users))


class Dinner(Base):
	__tablename__ = 'dinners'

	id = Column(Integer, primary_key = True)
	menu = Column(String)
	time = Column(DateTime)
	guests = Column(Integer)
	freeForAll = Column(Integer)
	cook = Column(Integer, ForeignKey('users.id'))
	group = Column(Integer, ForeignKey('groups.id'))

	cookUser = relationship("User")
	attendees = relationship(
					"User",
					secondary = attendees,
					backref = "dinners",
					primaryjoin	  = "Dinner.id == attendees.c.dinner",
					secondaryjoin = "attendees.c.user == User.id"
				)

	def __repr__(self):
		return "<Dinner %i : %s>" % (self.id, self.menu)

	def getAttendees(self):
		return [u for u in self.attendees if not u == self.cookUser]

	def getFuzzyTime(self):
		return "About %s:%s" % (self.getHour(), self.getFuzzyMin())

	def getDay(self):
		return self.time.strftime('%A')

	def getHour(self):
		return str(self.time.hour % 12)

	def getFuzzyMin(self): # Returns min to nearest 15.
		return ('0' + str((self.time.minute / 15) * 15))[-2:]
