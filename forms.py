from flask_security import RegisterForm
from flask_wtf import FlaskForm
from flask_security.forms import *
from wtforms.fields.core import IntegerField
from wtforms.fields.simple import TextField
from wtforms.validators import InputRequired
class registerForm(RegisterForm):
    username=StringField("Username", get_form_field_label('username'))

class addBook(FlaskForm):
    title=StringField("Book Title", validators=[InputRequired("Enter a Valid Title"), Length(max=255, message="Title Should be less than 255 charecters")])
    author= TextField("Authors", validators=[InputRequired("Enter a Valid Title")])
    price=IntegerField("Price", validators=[InputRequired("Enter a Valid Price")])
    stock= IntegerField("Available Stock", validators=[InputRequired("Enter the number of books available")])
    submit=SubmitField("Add Book")

class searchForm(FlaskForm):
    title=StringField("Book Title")
    submit=SubmitField("Search")

class addStock(FlaskForm):
    title=StringField("Book Title")
    stock=IntegerField("New Stock")
    submit=SubmitField("Add stock")