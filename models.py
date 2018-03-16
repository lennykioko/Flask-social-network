import datetime
from peewee import *
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
# Read more about UserMixin - 'http://flask-login.readthedocs.org/en/latest/#your-user-class'

# is all caps since we need it to be considered as a constant as we use it in our various modules
DATABASE = SqliteDatabase('social.db')

# classes can inherit from more than one parent class as such:
# UserMixin should come before Model
class User(UserMixin, Model):
    """Create a model for our users"""
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    # datetime lacks parenthesis so that it is run when the model is created and not when we run this script
    joined_at = DateTimeField(default=datetime.datetime.now) 
    is_admin = BooleanField(default=False)

    class Meta:
        database = DATABASE
        # the - sign orders it in descending order, the most recent people to join should be at the top
        # it is a tuple, no wonder it has the comma
        order_by = ('-joined_at',)
    
    def get_posts(self):
        return Post.select().where(Post.user == self)

    def get_stream(self):
        return Post.select().where(
            # << means inside of another set; all posts where the user is inside the people i follow
			(Post.user << self.following()) |
			(Post.user == self) # | means or
			)

    def following(self):
        """The users we are following"""
        # join connects various models from our database
        return(
            User.select().join(
            Relationship, on=Relationship.to_user
            ).where(
                Relationship.from_user == self
            )
        )

    def followers(self):
        """Users Following the current user"""
        return(
            User.select().join(
            Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )


    @classmethod # a method that can create a class of the class it exists in
    def create_user(cls, username, email, password, admin=False):
        """cls refers to the class, in our case it is User"""
        try:
            with DATABASE.transaction(): # transaction tries to create the user, if everything works, awesome, if not, it reverses what it just did, this prevents the error; your database is locked
                cls.create(
                username = username,
                email = email,	
                password = generate_password_hash(password), # never hold onto the actual passwords
                is_admin = admin
                )

        except IntegrityError: # raised when you try using an email or username that already exists
            raise ValueError("User already exists")

class Post(Model):
	timestamp = DateTimeField(default=datetime.datetime.now)
	user = ForeignKeyField(User, related_name='posts')
	content = TextField()

	class Meta:
		database = DATABASE
		order_by = ('-timestamp',) # most recent at the top

class Relationship(Model):
	from_user = ForeignKeyField(User, related_name='relationships') # people i am related to
	to_user = ForeignKeyField(User, related_name='related_to') # people related to me

	class Meta:
		database = DATABASE
        # tuple of the fields and boolean of whether the indexes are unique
		indexes = indexes = ((('from_user', 'to_user'), True),)

def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post, Relationship], safe=True)
    DATABASE.close()
