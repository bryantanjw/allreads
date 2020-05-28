import os
import requests
from flask import Flask, session,render_template, redirect, g, url_for, request, flash, jsonify
from flask_session import Session
from passlib.hash import pbkdf2_sha256

from wtform_fields import *
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from models import *


# Configure app
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config['TESTING'] = False
app.config['LOGIN_DISABLED'] = False

Session(app)
Bootstrap(app)

# Set up database
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://efjlliroqgsamc:d346a2f7b24d4390263c65449d9dd2baffd0a7bc03260e9fa114417525e62f5f@ec2-34-225-82-212.compute-1.amazonaws.com:5432/dd5h5alhd67p3l"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

@app.route("/", methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('search'))
        return '<h1>Invalid username or password</h1>'
    return render_template('index.html', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():  
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data

        # Hash password
        hashed_pswd = pbkdf2_sha256.hash(password)

        # Add user to DB
        user = User(username=username, password=hashed_pswd)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')

        return redirect(url_for('index'))

    return render_template("register.html", form=reg_form)



@app.route("/logout", methods=['GET'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have logged out successfully.', 'success')

    else:
        flash('You are not logged in.', 'danger')

    return redirect(url_for('index'))

     
@app.route("/search", methods=['GET', 'POST'])
def search():
    """ If the request is GET, render the page of search to the user with 10 books"""
    if current_user.is_authenticated:
        if request.method == "GET":
            books = db.session.execute("SELECT * FROM books").fetchmany(20)
            return render_template("search.html", books=books)

        else:
            """ If the request is POST, do the search with the text provided by the user """
            text = "%"+request.form.get("search-text")+"%"
            books = db.session.execute("SELECT * FROM books WHERE (LOWER(isbn) LIKE :isbn OR LOWER(title) LIKE :title OR LOWER(author) LIKE :author)", {"isbn":text.lower(), "title":text.lower(), "author":text.lower()}).fetchall()
            return render_template("search.html", books=books, search=text.replace('%', ''))

    else:
        flash('Please login before searching the database.', 'danger')
        return redirect(url_for('index'))


@app.route("/details/<isbn>", methods=["GET", "POST"])
@login_required
def details(isbn):
    form = ReviewForm()
    book = db.session.execute('SELECT title, author, year FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()
    if not book:
        return 'invalid ISBN'
    if request.method == 'POST':
        user_review = db.session.execute("SELECT * FROM reviews WHERE user_id= :user_id AND isbn= :isbn", {"user_id": current_user.id, "isbn": isbn}).fetchone()

        if user_review is not None:
            return render_template("error.html", message="You have already left a review on this book.", url_return='details/'+isbn, page_name=' book details')

        new_review = Reviews(user_id=current_user.id, isbn=isbn, review_text=form.review_text.data,
                             rating=form.rating.data)
        db.session.add(new_review)
        db.session.commit()
    title, author, year = book
    d = {'isbn': isbn, 'title': title, 'author': author, 'year': year}
    good_reads = good_reads_data(isbn)
    reviews = Reviews.query.filter_by(isbn=isbn).all()
    user = db.session.execute("SELECT users.username FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id").fetchall()
    return render_template('details.html', book=d, good_reads=good_reads, form=form, reviews=reviews,
                           name=current_user.username, user=user)


def good_reads_data(isbn):
    url = "https://www.goodreads.com/book/review_counts.json"
    res = requests.get(url, params={"key": "YxCmT9hdATcXpR5XmXAutQ", "isbns": isbn})
    if res.status_code == 200:
        return res.json()['books'][0]


# Page for the website's API
@app.route("/api/<ISBN>", methods=["GET"])
def api(ISBN):
    book = db.session.execute("SELECT * FROM books WHERE isbn = :ISBN", {"ISBN": ISBN}).fetchone()
    if book is None:
        return render_template("error.html", message="We detected an invalid ISBN. "
                                                           "Please try again.", url_return='index', page_name='Homepage')
    reviews = db.session.execute("SELECT * FROM reviews").fetchall()
    count = 0
    rating = 0
    for review in reviews:
        count += 1
        rating += review.rating
    if count:
        average_rating = rating / count
    else:
        average_rating = 0

    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_score=average_rating
    )



if __name__ == '__main__':
    app.run()
