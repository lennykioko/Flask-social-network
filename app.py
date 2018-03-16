from flask import (Flask, g, render_template, flash, redirect, url_for, abort)
from flask_bcrypt import check_password_hash
from flask_login import (LoginManager, login_user, logout_user, 
							login_required, current_user)

import forms
import models

app = Flask(__name__)

# secret_key is a random string of alphanumerics
app.secret_key = "awerewf22323*&^%^&$eefdl;ikdjfkldf(ggf=0"
DEBUG = True

# set up the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
	try:
		return models.User.get(models.User.id == userid)
	except models.DoesNotExist:
		return None

@app.before_request
def before_request():
	"""Connect to database before each request"""
    # g allows us to have global objects that will be accessible everywhere even in different modules eg views.py
	g.db = models.DATABASE
	g.db.connect()
	g.user = current_user

@app.after_request
def after_request(response):
	"""close database connection after each request"""
    # response automatically sets itself to the value of return from your view function
	g.db.close()
	return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("Successful Registration", "success")
        models.User.create_user(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data
        )
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = forms.LoginForm()
	if form.validate_on_submit():
		try:
			user = models.User.get(models.User.email == form.email.data)
		except models.DoesNotExist:
            # we have an ambigous message so as not to make a hacker's work easier
			flash("Your email or password does not match", "error")
		else:
			if check_password_hash(user.password, form.password.data):
				login_user(user) # logs in user and sets up sessions and cookies for our user automatically
				flash("Successfully Logged In", "success")
				return redirect(url_for('index'))
			else:
				flash("Your email or password does not match", "error")
                
	return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
	logout_user() # deletes cookies and sessions created by login_user()
	flash("You have been logged out.", "success")
	return redirect(url_for('login'))

@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
	form = forms.PostForm()
	if form.validate_on_submit():
		models.Post.create(user=g.user.id, content=form.content.data.strip())
		flash("Message Posted: Thanks!", "success")
		return redirect(url_for('index'))
	return render_template('post.html', form=form)

@app.route('/')
def index():
	stream = models.Post.select().limit(100)
	return render_template('stream.html', stream=stream)

@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
	template = 'stream.html'
	if username and username != current_user.username:
		try:
			user = models.User.select().where(models.User.username**username).get()
			# ** makes the comparison case-insensitive
		except models.DoesNotExist:
			abort(404)
		else:
			stream = user.posts.limit(100)
	else:
		stream = current_user.get_stream().limit(100)
		user = current_user
	if username:
		template = 'user_stream.html'
	return render_template(template, stream=stream, user=user)

@app.route('/post/<int:post_id>')
def view_post(post_id):
	posts = models.Post.select().where(models.Post.id==post_id)
	if posts.count() == 0:
		abort(404)
	return render_template('stream.html', stream=posts)

@app.route('/follow/<username>')
@login_required
def follow(username):
	try:
		to_user = models.User.get(models.User.username**username)
	except models.DoesNotExist:
		abort(404)
	else:
		try:
			models.Relationship.create(
				from_user = g.user._get_current_object(),
				to_user = to_user
				)
		except models.IntegrityError: # raised when you try following someone you are already following
			pass # no big deal, just pass
		else:
			flash("You are now following {}".format(to_user.username), "success")
	return redirect(url_for('stream', username=to_user.username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
	try:
		to_user = models.User.get(models.User.username**username)
	except models.DoesNotExist:
		abort(404)
	else:
		try:
			models.Relationship.get(
				from_user = g.user._get_current_object(),
				to_user = to_user
				).delete_instance()
		except models.IntegrityError:
			pass
		else:
			flash("You have unfollowed {}".format(to_user.username), "success")
	return redirect(url_for('stream', username=to_user.username))

@app.errorhandler(404)
def not_found(error):
	return render_template('404.html'), 404

if __name__ == '__main__':
    models.initialize()
    try:
        # create_user will hash our passwords
        models.User.create_user(
        username = 'lenny',
        email = 'lennykmutua@gmail.com',
        password = 'password',
        admin = True
        )
    except ValueError:
        pass

    app.run(debug=DEBUG)