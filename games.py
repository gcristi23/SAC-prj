from flask import Flask, render_template, request, session
import os, json
from flask_sqlalchemy import SQLAlchemy, BaseQuery, _QueryProperty
from models import Base, User, Game
import numpy as np

app = Flask(__name__)

games = None
logged_user = None
costs = None
top_10k = None

SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

class PrintQuery(BaseQuery):
	def __iter__(self):
		print(self)
		return super(PrintQuery, self).__iter__()

app.config.from_object(__name__)
db = SQLAlchemy(app)
db.Model = Base
db.Model.query_class = PrintQuery
db.Model.query = _QueryProperty(db)
db.session.expunge_all()

@app.route('/')
def index():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		html_page = render_template("front.html", **{
				'games': games,
				'logged_user': logged_user
		})

		return html_page

@app.route("/select" , methods=['GET', 'POST'])
def select():
	global logged_user
	global games

	game_name = request.args.get("comp_select")
	if game_name not in games:
		return game_selection_error()

	user = logged_user
	game = Game(name=game_name, user=user)
	user.games.append(game)

	try:
		db.session.add(game)
	except Exception as e:
		print(e)
	
	db.session.commit()

	return my_games()

@app.route("/error" , methods=['GET', 'POST'])
def game_selection_error():
	return render_template("error.html")

@app.route("/my_games" , methods=['GET', 'POST'])
def my_games():
	global logged_user

	user = db.session.query(User).filter(User.email == logged_user.email).first()

	game_recs = []
	for game in user.games:
		k = np.max(costs[top_10k[game.name][0]])
		the_id = np.where(costs[top_10k[game.name][0]] == k)

		rez = []
		print(len(the_id[0]))
		for k in the_id[0]:
			if len(rez) >= 5:
				break
			for x in games:
				if top_10k[x][0] == k:
					rez.append(x)

		game_recs.append((game.name, rez))

	with app.test_request_context():
		html_page = render_template("my_games.html", **{
				'user': user,
				'games': game_recs
		})

		return html_page

@app.route('/login', methods=['POST'])
def login():
	global logged_user

	email = request.form['email']
	logged_user = db.session.query(User).filter(User.email == email).first()

	if logged_user != None:
		session['logged_in'] = True

	return index()

@app.route('/signup', methods=['POST'])
def signup():
	global logged_user

	email = request.form['email']
	name = request.form['name']

	with app.test_request_context():
		user = User(name=name, email=email)
		logged_user = user
		try:
			db.session.add(user)
			db.session.commit()
		except Exception as e:
			print(e)

	session['logged_in'] = True

	return index()

@app.route("/logout")
def logout():
	global logged_user
	
	session['logged_in'] = False
	logged_user = None
	return index()

if __name__ == '__main__':
	db.create_all()

	with open('costs.txt', 'r') as s:
		text = s.read()
		text = text.replace('\n', '')
		text = text.replace('  ', ' ')
		lists = text[1:-1].split('] [')
		print(len(lists))

		lists[0] = lists[0][1:]
		lists[-1] = lists[-1][:-1]
		costs = []
		for l in lists:
			parsed = l.split()
			costs.append([int(x) for x in parsed])

	with open('top10k.txt') as f:
		top_10k = json.load(f)
	games = [x for x in top_10k.keys()]

	costs = np.array(costs)
	app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
	app.secret_key = os.urandom(12)
	app.run(debug=True)