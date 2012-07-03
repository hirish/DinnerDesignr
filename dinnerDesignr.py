from flask import Flask, g, url_for, redirect, request, session
from random import choice
import string
from flaskext.mako import init_mako, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from views import *
from models import *

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = "I am awesome sauce" # For sessions

init_mako(app)
engine = create_engine('mysql://root:@localhost/DinnrDesignr')
S = sessionmaker(bind=engine)
s = S()

@app.route('/', methods=['POST','GET'])
@app.route('/login', methods=['POST','GET'])
@app.route('/register', methods=['POST','GET'])
def index():
	registrationError = None
	loginError = None
	if request.method == 'POST':

		name = request.form.get('name', default = "").lower()
		email = request.form.get('email').lower()
		password = request.form.get('password')

		if request.form.get('register'): # Registration
			try:
				return register(name, email, password)
			except Exception as e:
				registrationError = e
		elif request.form.get('login'): # Login
			try:
				return login(email, password)
			except Exception as e:
				loginError = e

	return render_template('login.html', registrationError = registrationError, loginError = loginError)

def getUser(userId):
	return s.query(User).filter(User.id == userId)[0]

def isLoggedIn():
	try:
		return s.query(User).filter(User.email == session['email'])[0]
	except KeyError:
		return None

##### User Management #####

def register(name, email, password):
	print "Registration event detected"
	newUser = User(name, email, password)

	if s.query(User).filter(User.email == newUser.email).all():
		raise Exception("An account has already been registered with that email address.")

	s.add(newUser)
	s.commit()
	print "Registered", email

	return login(email, password)

def login(email, password):
	print "Login event detected"
	user = s.query(User).filter(User.email == email).all()

	if not user:
		raise Exception("That Username doesn't exist. Care to register it below?")

	if not user[0].checkPassword(password):
		raise Exception("You typed your password wrong! Try again?")

	session['email'] = email
	print "Logged in as", email
	if not user[0].group:
		return redirect(url_for('groups'))
	return redirect(url_for('menu'))

@app.route('/logout')
def logout():
	session.pop('email', None)
	return redirect('/')

###### Menu Management ######

@app.route('/menu')
def menu():
	user = isLoggedIn()
	if not user:
		return redirect('/')
	
	dinners = user.g.dinners[:10]
	print dinners

	return render_template('menu.html', dinners = dinners)

@app.route('/update', methods=["GET"])
@app.route('/update.html', methods=["GET"])
def form():
	user = isLoggedIn()
	if not user:
		return redirect('/')

	id = request.args.get('id', default=None)
	if not id:
		raise Exception("No dinner ID was specified.")
	try:
		dinner = s.query(Dinner).filter(Dinner.id == id)[0]
		if not user.group == dinner.group:
			raise Exception("You do not have the rights to edit this meal.")
		return render_template('form.html', dinner = dinner)
	except KeyError:
		raise Exception("That dinner ID does not exist!")

@app.route('/submitUpdate', methods=["POST"])
def updateDinner():
	user = isLoggedIn()
	if not user:
		return redirect('/')

	id = request.form.get('dinner', default = None)
	if not id:
		raise Exception("No dinner ID was specified.")
	try:
		dinner = s.query(Dinner).filter(Dinner.id == id)[0]
	except IndexError:
		raise Exception("That dinner ID does not exist!")

	if not user.group == dinner.group:
		raise Exception("You do not have the rights to edit this meal.")

	cook = int(request.form.get('cook'))
	try:
		cookUser = getUser(cook)
		print "Cook", cookUser
	except IndexError:
		raise Exception("Cook user invalid")

	if not cookUser.group == dinner.group:
		raise Exception("Cook user invalid")

	attendees = request.form.getlist('attendee')
	attendees = [getUser(int(attendee)) for attendee in attendees]
	if not cookUser in attendees:
		attendees += [cookUser]
	
	hour = int(request.form.get('hour'))
	minute = int(request.form.get('minute'))
	menu = request.form.get('menu')
	guests = int(request.form.get('guests'))

	freeForAll = request.form.get('free', default=0)
	if freeForAll:
		freeForAll = 1
	
	print 'Free For All: ', freeForAll

	dinner.time = dinner.time.replace(hour = hour, minute = minute)
	dinner.menu = menu
	dinner.freeForAll = freeForAll
	dinner.attendees = attendees
	dinner.cookUser = cookUser
	dinner.guests = guests

	s.commit()

	return """<script type="text/javascript" language="javascript">
	        if (top.frames.length>0)
					setTimeout("top.location = '%s%s';",100);
			</script>""" % ('http://localhost:5000', url_for('menu'))
	return redirect(url_for('menu'))

####### Group Management ########

@app.route('/groups')
def groups():
	user = isLoggedIn()
	if not user:
		return redirect('/')

	return render_template('group.html')

@app.route('/joinGroup', methods=["GET"])
def joinGroup(code = None):
	user = isLoggedIn()
	if not user:
		return redirect('/')

	code = request.args.get('code', default = None)
	print code
	if not code:
		return redirect(url_for('groups'))
	try:
		group = s.query(Group).filter(Group.code == code)[0]
	except IndexError:
		return render_template('group.html', codeError = "The code beginning \"%s\" is not valid." % code[:10])

	user.g = group
	s.commit()

	return redirect(url_for('menu'))

@app.route('/createGroup')
def createGroup():
	user = isLoggedIn()
	if not user:
		return redirect('/')

	code = ''.join([choice(string.letters + string.digits) for i in range(64)])
	if (len(s.query(Group).filter(Group.code == code).all()) > 0):
		code = ''.join([choice(string.letters + string.digits) for i in range(64)])
	g = Group(code = code)
	s.add(g)
	s.commit()
	return joinGroup(code)

if __name__ == '__main__':
	app.run(host="0.0.0.0")
