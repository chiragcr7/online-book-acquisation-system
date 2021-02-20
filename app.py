from flask import Flask, redirect, url_for, render_template, flash, request
from flask_admin.contrib.sqla.view import ModelView
from flask_security.forms import PasswordField
from flask_security import Security, login_required, \
     SQLAlchemySessionUserDatastore, roles_required, current_user, utils, UserMixin, RoleMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from forms import registerForm, addBook, searchForm, addStock
from flask_admin import Admin
from flask_admin.contrib import sqla
import os


app = Flask(__name__)
app.config.from_pyfile('config.cfg')

db=SQLAlchemy(app)


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
                         backref=db.backref('users', lazy='dynamic'))
    def __repr__(self):
        return '<User %r>' % self.username

class bookdata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(255), unique=True)
    author=db.Column(db.Text(255))
    price=db.Column(db.Integer)
    stock=db.Column(db.Integer)

class orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(255))
    book_id=db.Column(db.Integer)
    title=db.Column(db.String(255))
    author=db.Column(db.Text(255))
    price=db.Column(db.Integer)

class wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(255))
    book_id=db.Column(db.Integer)
    title=db.Column(db.String(255))
    author=db.Column(db.Text(255))
    price=db.Column(db.Integer)

user_datastore = SQLAlchemySessionUserDatastore(db.session,
                                                User, Role)
security = Security(app, user_datastore, register_form=registerForm)


# Create a user to test with

class UserAdmin(sqla.ModelView):

    # Don't display the password on the list of Users
    column_exclude_list = ('password',)

    # Don't include the standard password field when creating or editing a User (but see below)
    form_excluded_columns = ('password',)

    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdmin, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.encrypt_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(sqla.ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

# Initialize Flask-Admin
admin = Admin(app)

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
admin.add_view(ModelView(bookdata, db.session))
admin.add_view(ModelView(orders, db.session))
admin.add_view(ModelView(wishlist, db.session))

@app.before_first_request
def create_user():
    try:
        db.create_all()
        admin_user=user_datastore.create_user(email='admin@test.com', username='admin15', password='admintest', last_login_at=datetime.now(), \
            current_login_at=datetime.now(), last_login_ip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr), current_login_ip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr), login_count=0, confirmed_at=datetime.now() )
        admin=user_datastore.find_or_create_role('admin')
        user=user_datastore.find_or_create_role('user')
        user_datastore.add_role_to_user(admin_user, admin)
        db.session.commit()
    except:
        pass
    

# Views
@app.route('/')
@login_required
def home():
    if current_user.has_role('admin'):
        return render_template('admin/index_admin.html')
    form=searchForm()
    return render_template('user/index.html', form=form)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form=searchForm()
    book=form.title.data
    results=db.session.query(bookdata).filter(bookdata.title.like("%{}%".format(book)))
    return render_template('view/search.html', results=results, form=form)

@app.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def addBooks():
    form=addBook()
    return render_template('admin/addBooks.html', form=form)

@app.route('/addstock', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def addStocks():
    form=addStock()
    return render_template('admin/addStock.html', form=form)

@app.route('/addbook', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def addbooks():
    form=addBook()

    book=bookdata(title=form.title.data, author= form.author.data, price=form.price.data, stock= form.stock.data)
    db.session.add(book)
    db.session.commit()
    flash('Book added Sucessfully', 'success')
    return redirect('/add')

@app.route('/addNewStock', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def addNewStock():
    form=addStock()
    book_obj=bookdata.query.filter_by(title=form.title.data).first()
    book_obj.stock+=form.stock.data
    db.session.commit()
    flash('New Stock Added', 'success')
    return redirect('/addstock')
@app.route('/buy/<int:id>', methods=['GET', 'POST'])
@login_required
def buy(id):
    
    book_obj=bookdata.query.filter_by(id=id).first()
    if book_obj.stock>0:
        obj=orders(username=current_user.username, book_id=id, title=book_obj.title, author=book_obj.author, price=book_obj.price)
        book_obj.stock-=1
        flash('Ordered Sucessfully', 'Success')
    else:
        obj=wishlist(username=current_user.username, book_id=id, title=book_obj.title, author=book_obj.author, price=book_obj.price)
        flash('Added to wishlist Sucessfully', 'Success')
    db.session.add(obj)
    db.session.commit()
    
    return redirect('/add')

@app.route('/orders', methods=['GET', 'POST'])
@login_required
def view_orders():

    if current_user.has_role('admin'):
        all_orders=orders.query.all()
        return render_template('view/orders.html', orders=all_orders)
    else:
        form=searchForm()
        all_orders=orders.query.filter_by(username=current_user.username).all()
        return render_template('view/orders.html', orders=all_orders, form=form)

@app.route('/wishlist', methods=['GET', 'POST'])
@login_required
def wishlists():
    if current_user.has_role('admin'):
        all_orders=wishlist.query.all()
        return render_template('view/wishlist.html', orders=all_orders)
    else:
        form=searchForm()
        all_orders=wishlist.query.filter_by(username=current_user.username).all()
        return render_template('view/wishlist.html', orders=all_orders,form= form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out Successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)