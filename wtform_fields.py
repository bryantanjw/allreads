from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, FloatField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError
from passlib.hash import pbkdf2_sha256

from flask_bootstrap import Bootstrap

from models import *


def invalid_credentials(form, field):
    """ Username and password checker """

    password = field.data
    username = form.username.data

    # Check username is invalid
    user_data = User.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Username or password is incorrect")

    # Check password in invalid
    elif not pbkdf2_sha256.verify(password, user_data.password):
        raise ValidationError("Username or password is incorrect")


class RegistrationForm(FlaskForm):
    """ Registration form """

    username = StringField('username',
        validators=[InputRequired(message="Username required."),
        Length(min=4, max=15, message="Username must be between 4 to 15 characters.")])
    
    password = PasswordField('password',
        validators=[InputRequired(message="Password required."),
        Length(min=4, max=80, message="Password must be between 4 to 80 characters.")])
    
    confirm_pswd = PasswordField(u'Confirm Password', 
        validators=[InputRequired(message="Password required."),
        EqualTo('password', message="Passwords must match.")])


    def validate_username(self, username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError("Username already exists.")


class LoginForm(FlaskForm):
    """ Login form """

    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), invalid_credentials])
    remember = BooleanField('remember me')


class BookSearchForm(FlaskForm):
    option = SelectField(u'Choose a search option',  choices = [('isbn', 'ISBN'),
                                        ('title', 'Title'),
                                        ('author', 'Author')])


class ReviewForm(FlaskForm):
    review_text = StringField('review_text', validators=[InputRequired(), Length(min=10, max=10000)])
    rating = FloatField('rating', validators=[InputRequired()])

