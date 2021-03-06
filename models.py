from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import hashlib, datetime

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

	def getOwned(self):
		try:
			return self.owned[0]
		except IndexError:
			return None

	def gravatar(self):
		return hashlib.md5(self.email.strip().lower()).hexdigest()


class Group(Base):
	__tablename__ = 'groups'

	id = Column(Integer, primary_key=True)
	code = Column(String)
	owner = Column(Integer, ForeignKey('users.id'))
	users = relationship("User", backref="g", primaryjoin = "users.c.group == groups.c.id")
	dinners = relationship("Dinner", backref="g")
	ownerUser = relationship("User", backref="owned", primaryjoin = "users.c.id == groups.c.owner")

	def __repr__(self):
		return "<Group %i : %s>" % (self.id, str(self.users))

	def getDinners(self):
		today = datetime.datetime.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
		return sorted([d for d in self.dinners if d.time >= today], key = lambda d: d.time)


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
