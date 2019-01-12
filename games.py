import json
import os

import numpy as np
import requests as rq
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy, BaseQuery, _QueryProperty

from models import Base, User, Game

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
	global logged_user
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		games_owned = []
		user = db.session.query(User).filter(User.email == logged_user.email).first()
		for game in user.games:
			games_owned.append(game.name)
		html_page = render_template("front.html", **{
			'games': list(set(games) - set(games_owned)),
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
	game = db.session.query(Game).filter(Game.name == game_name).first()
	user.games.append(game)

	try:
		db.session.commit()
	except Exception as e:
		print(e)
	


	return my_games()

@app.route("/error" , methods=['GET', 'POST'])
def game_selection_error():
	return render_template("error.html")

@app.route("/my_games" , methods=['GET', 'POST'])
def my_games():
	global logged_user

	user = db.session.query(User).filter(User.email == logged_user.email).first()
	games_owned = []
	game_recs = None
	for game in user.games:
		k = np.max(costs[top_10k[game.name][0]])
		the_id = np.where(costs[top_10k[game.name][0]] == k)

		rez = []
		for k in the_id[0]:
			if len(rez) >= 5:
				break
			for x in games:
				if top_10k[x][0] == k:
					rez.append(x)
		games_owned.append(game.name)
		if game_recs is None:
			game_recs = set(rez)
		else:
			game_recs = game_recs | set(rez)
	if game_recs is None:
		game_recs = []
	else:
		game_recs = list(game_recs - set(games_owned))
	with app.test_request_context():
		html_page = render_template("my_games.html", **{
			'user': user.name,
				'games': game_recs
		})
		return html_page


@app.route('/steam', methods=['POST'])
def steam():
	global logged_user

	steam = request.form['steam']

	data = rq.get("https://steamcommunity.com/id/%s/?xml=1" % steam)
	logged_user = db.session.query(User).filter(User.name == steam).first()
	try:
		id64 = data.text.split("ID64>")[1].split("<")[0]
	except:
		return index()
	data = rq.get(
		"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=C6BBD644E5F37D478E0AF48934CBD4EE&steamid={}&format=json".format(
			id64))
	try:
		games_steam = json.loads(data.text)['response']['games']
	except:
		return index()
	games_owned = []
	game_a = {}
	for g in games_steam:
		time_played = (g['playtime_forever'] + 1) / 5.0
		game = db.session.query(Game).filter(Game.steam_id == g['appid']).first()
		if game is None: continue
		k = np.max(costs[top_10k[game.name][0]])
		the_id = np.where(costs[top_10k[game.name][0]] == k)

		rez = []

		for k in the_id[0]:
			if len(rez) >= 5:
				break
			for x in games:
				if top_10k[x][0] == k:
					rez.append(x)
		games_owned.append(game.name)
		for x in rez:
			if x in game_a:
				game_a[x][0] += 1
				game_a[x][1] += time_played
			else:
				game_a[x] = [1, time_played]
	top_recs = sorted([(x, y[0] * y[1]) for x, y in game_a.items()], key=lambda x: x[1], reverse=True)
	print(steam)
	print(top_recs)
	game_recs = set([x[0] for x in top_recs])
	game_recs = list(game_recs - set(games_owned))

	with app.test_request_context():
		html_page = render_template("my_games.html", **{
			'user': steam,
			'games': game_recs[:10]
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

		lists[0] = lists[0][1:]
		lists[-1] = lists[-1][:-1]
		costs = []
		for l in lists:
			parsed = l.split()
			costs.append([int(x) for x in parsed])

	with open('top10k.txt') as f:
		top_10k = json.load(f)
	games = [x for x in top_10k.keys()]
	# to_insert = []
	# games_ids = {x[1]:y for y, x in top_10k.items()}
	# for st_id, game in games_ids.items():
	# 	to_insert.append(Game(name = game, steam_id  = st_id))
	# db.session.bulk_save_objects(to_insert)
	# db.session.commit()
	costs = np.array(costs)
	app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
	app.secret_key = os.urandom(12)
	app.run(debug=True)