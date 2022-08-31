from . import db

class Player(db.Model):
    __tablename__ = 'padelPlayers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    rating = db.Column(db.Integer)
    rating_by_rounds = db.Column(db.Integer)


class RatingHistory(db.Model):
    __tablename__ = 'padelRatingHistory'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    game_id = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    rating_by_rounds = db.Column(db.Integer)
    rating_diff = db.Column(db.Integer)
    rounds_rating_diff = db.Column(db.Integer)
    datetime = db.Column(db.String)


class Game(db.Model):
    __tablename__ = 'padelGames'
    id = db.Column(db.Integer, primary_key=True)
    team1 = db.Column(db.String) # "3,2"
    team2 = db.Column(db.String) # "0,1"
    score = db.Column(db.String) # "6,0" team1points, team2points
    datetime = db.Column(db.String)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String)
    username = db.Column(db.String)
