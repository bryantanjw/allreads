from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
	""" User model """

	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique=True, nullable=False)
	password = db.Column(db.String(), nullable=False)
	
	def __repr__(self):
		return '<User {}>'.format(self.username)


class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    isbn = db.Column(db.String(10))
    review_text = db.Column(db.String(10000), nullable=False)
    rating = db.Column(db.Float())