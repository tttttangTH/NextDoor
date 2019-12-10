from hashlib import md5
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


# from app.friends import get_friend_requests


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def num_request(self):
        received_friend_requests = db.session.query(User).filter(Connection.user_b_id == self.id,
                                                                 Connection.status == "Requested").join(Connection,
                                                                                                        Connection.user_a_id == User.id).all()

        sent_friend_requests = db.session.query(User).filter(Connection.user_a_id == self.id,
                                                             Connection.status == "Requested").join(Connection,
                                                                                                    Connection.user_b_id == User.id).all()
        return len(received_friend_requests) + len(sent_friend_requests)

    def num_receive_request(self):
        received_friend_requests = db.session.query(User).filter(Connection.user_b_id == self.id,
                                                                 Connection.status == "Requested").join(Connection,
                                                                                                        Connection.user_a_id == User.id).all()
        return len(received_friend_requests)

    def num_sent_request(self):
        sent_friend_requests = db.session.query(User).filter(Connection.user_a_id == self.id,
                                                             Connection.status == "Requested").join(Connection,
                                                                                                    Connection.user_b_id == User.id).all()

        return len(sent_friend_requests)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    # back是反向引用,User和Post是一对多的关系，backref是表示在Post中新建一个属性author，关联的是Post中的user_id外键关联的User对象。
    # lazy属性常用的值的含义，select就是访问到属性的时候，就会全部加载该属性的数据;joined则是在对关联的两个表进行join操作，从而获取到所有相关的对象;dynamic则不一样，在访问属性的时候，并没有在内存中加载数据，而是返回一个query对象, 需要执行相应方法才可以获取对象，比如.all()
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<???:{}>'.format(self.username)


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Connection(db.Model):
    """Connection between two users to establish a friendship and can see each other's info."""

    __tablename__ = "connections"

    connection_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_a_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_b_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)

    # When both columns have a relationship with the same table, need to specify how
    # to handle multiple join paths in the square brackets of foreign_keys per below
    user_a = db.relationship("User", foreign_keys=[user_a_id], backref=db.backref("sent_connections"))
    user_b = db.relationship("User", foreign_keys=[user_b_id], backref=db.backref("received_connections"))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Connection connection_id=%s user_a_id=%s user_b_id=%s status=%s>" % (self.connection_id,
                                                                                      self.user_a_id,
                                                                                      self.user_b_id,

                                                                                      self.status)


def is_friends_or_pending(user_a_id, user_b_id):
    """
    Checks the friend status between user_a and user_b.
    Checks if user_a and user_b are friends.
    Checks if there is a pending friend request from user_a to user_b.
    """

    is_friends = db.session.query(Connection).filter(Connection.user_a_id == user_a_id,
                                                     Connection.user_b_id == user_b_id,
                                                     Connection.status == "Accepted").first()

    is_pending = db.session.query(Connection).filter(Connection.user_a_id == user_a_id,
                                                     Connection.user_b_id == user_b_id,
                                                     Connection.status == "Requested").first()

    return is_friends, is_pending


def get_friend_requests(user_id):
    """
    Get user's friend requests.
    Returns users that user received friend requests from.
    Returns users that user sent friend requests to.
    """

    received_friend_requests = db.session.query(User).filter(Connection.user_b_id == user_id,
                                                             Connection.status == "Requested").join(Connection,
                                                                                                    Connection.user_a_id == User.id).all()

    sent_friend_requests = db.session.query(User).filter(Connection.user_a_id == user_id,
                                                         Connection.status == "Requested").join(Connection,
                                                                                                Connection.user_b_id == User.id).all()

    return received_friend_requests, sent_friend_requests


def get_friends(user_id):
    """
    Return a query for user's friends
    Note: This does not return User objects, just the query
    """

    friends = db.session.query(User).filter(Connection.user_a_id == user_id,
                                            Connection.status == "Accepted").join(Connection,
                                                                                  Connection.user_b_id == User.id)

    return friends
