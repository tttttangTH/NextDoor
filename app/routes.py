from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user
from app.forms import LoginForm, PostForm
from app.models import User, Post, Connection, is_friends_or_pending, get_friends, get_friend_requests
from flask_login import logout_user
from flask_login import login_required
from flask import request
from werkzeug.urls import url_parse
from app.forms import RegistrationForm
from app import app, db
from datetime import datetime
from app.forms import EditProfileForm
from sqlalchemy_searchable import search
from app import csrf
# from app.friends import is_friends_or_pending, get_friend_requests, get_friends


@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')


# 建立路由，通过路由可以执行其覆盖的方法，可以多个路由指向同一个方法。

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None

    # posts = current_user.followed_posts().all()
    return render_template('index.html', title='tth', form=form, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码')
            return redirect(url_for('login'))
        # 重定向至首页
        login_user(user, remember=form.remember_me.data)

        # received_friend_requests, sent_friend_requests = get_friend_requests(current_user.id)
        # num_received_requests = len(received_friend_requests)
        # num_sent_requests = len(sent_friend_requests)
        # num_total_requests = num_received_requests + num_sent_requests
        #
        #

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # 判断当前用户是否验证，如果通过的话返回首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('New user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None

    total_friends = len(get_friends(user.id).all())

    # user_a_id = session["current_user"]["user_id"]
    user_a_id = current_user.id
    user_b_id = user.id
    friends, pending_request = is_friends_or_pending(user_a_id, user_b_id)
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url,
                           total_friends=total_friends,
                           friends=friends,
                           pending_request=pending_request
                           )


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile '))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/explore')
# @login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None

    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add_friend/<username>')
@login_required
def add_friend(username):
    """Send a friend request to another user."""
    user = User.query.filter_by(username=username).first()
    user_a_id = current_user.id
    user_b_id = user.id
    # print(user_b_id, "sss")
    # print(request.form)
    # Check connection status between user_a and user_b
    is_friends, is_pending = is_friends_or_pending(user_a_id, user_b_id)

    if user_a_id == user_b_id:
        flash("You cannot add yourself as a friend.")

    elif is_friends:
        flash("You are already friends.")

    elif is_pending:
        flash("Your friend request is pending.")

    else:
        requested_connection = Connection(user_a_id=user_a_id,
                                          user_b_id=user_b_id,
                                          status="Requested")
        db.session.add(requested_connection)
        db.session.commit()
        flash('You have sent a friend request to {}.'.format(username))

        return redirect(url_for('user', username=username))


@app.route('/accept_friend/<username>')
@login_required
def accept_friend(username):
    """Send a friend request to another user."""
    user = User.query.filter_by(username=username).first()
    user_a_id = current_user.id
    user_b_id = user.id
    # print(user_b_id, "sss")
    # print(request.form)
    # Check connection status between user_a and user_b
    sender = db.session.query(Connection).filter(Connection.user_a_id == user_b_id,
                                                 Connection.user_b_id == user_a_id,
                                                 Connection.status == "Requested").first()
    sender.status = "Accepted"
    db.session.commit()
    new_connection = Connection(user_a_id=user_a_id,
                                user_b_id=user_b_id,
                                status="Accepted")
    db.session.add(new_connection)
    db.session.commit()
    flash('You have A new friend'.format(username))

    return redirect(url_for('show_friends_and_requests'))


@app.route('/decline_friend/<username>')
@login_required
def decline_friend(username):
    """Send a friend request to another user."""
    user = User.query.filter_by(username=username).first()
    user_a_id = current_user.id
    user_b_id = user.id
    # print(user_b_id, "sss")
    # print(request.form)
    # Check connection status between user_a and user_b
    sender = db.session.query(Connection).filter(Connection.user_a_id == user_b_id,
                                                 Connection.user_b_id == user_a_id,
                                                 Connection.status == "Requested").first()
    db.session.delete(sender)
    db.session.commit()
    # new_connection = Connection(user_a_id=user_a_id,
    #                             user_b_id=user_b_id,
    #                             status="Accepted")
    # db.session.add(new_connection)
    # db.session.commit()
    # flash('You have A new friend'.format(username))

    return redirect(url_for('show_friends_and_requests'))


@app.route('/cancer_friend/<username>')
@login_required
def cancer_friend(username):
    """Send a friend request to another user."""
    user = User.query.filter_by(username=username).first()
    user_a_id = current_user.id
    user_b_id = user.id
    # print(user_b_id, "sss")
    # print(request.form)
    # Check connection status between user_a and user_b
    sender = db.session.query(Connection).filter(Connection.user_a_id == user_a_id,
                                                 Connection.user_b_id == user_b_id,
                                                 Connection.status == "Requested").first()
    db.session.delete(sender)
    db.session.commit()
    # new_connection = Connection(user_a_id=user_a_id,
    #                             user_b_id=user_b_id,
    #                             status="Accepted")
    # db.session.add(new_connection)
    # db.session.commit()
    # flash('You have A new friend'.format(username))

    return redirect(url_for('show_friends_and_requests'))


@app.route("/friends")
@login_required
def show_friends_and_requests():
    """Show friend requests and list of all friends"""
    # current_user.update_para()
    # This returns User objects for current user's friend requests
    received_friend_requests, sent_friend_requests = get_friend_requests(current_user.id)
    friends = get_friends(current_user.id)

    return render_template("friends.html", received_friend_requests=received_friend_requests,
                           sent_friend_requests=sent_friend_requests,
                           friends=friends)


@app.route("/friends/search", methods=["GET"])
def search_users():
    """Search for a user by email and return results."""

    # Returns users for current user's friend requests
    received_friend_requests, sent_friend_requests = get_friend_requests(current_user.id)

    # Returns query for current user's friends (not User objects) so add .all() to the end to get list of User objects
    friends = get_friends(current_user.id).all()

    user_input = request.args.get("q")

    # Search user's query in users table of db and return all search results
    search_results = search(db.session.query(User), user_input).all()

    return render_template("friends_search_results.html",
                           received_friend_requests=received_friend_requests,
                           sent_friend_requests=sent_friend_requests,
                           friends=friends,
                           search_results=search_results)