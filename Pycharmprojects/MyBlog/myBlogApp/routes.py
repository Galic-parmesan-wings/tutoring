import json
import os
import secrets
from datetime import datetime
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, abort, jsonify, g, current_app
from flask_cors import cross_origin
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from myBlogApp import app, db, mail
from myBlogApp.email import send_password_reset_email
from myBlogApp.form import LoginForm, RegistrationForm, UpdateProfileForm, CreateNewPost, AddComments, ReplyForm, \
    SearchForm, ResetPasswordRequestForm, ResetPasswordForm, MessageForm
from myBlogApp.models import User, Post, Comment, Message, Notification


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html', title='Index')


@app.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=5)
    return render_template('home.html', title='Home', posts=posts)


@app.route('/user/<string:username>/following')
@login_required
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    followings = user.followed.all()
    num = user.followed.count()
    return render_template('following.html', followings=followings, num=num, user=user)


@app.route('/user/<string:username>/followers')
@login_required
def show_follower(username):
    user = User.query.filter_by(username=username).first_or_404()
    followers = user.followers.all()
    num = user.followers.count()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).paginate(page=page, per_page=5)
    return render_template('followers.html', followers=followers, num=num, user=user, posts=posts)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=5)
    return render_template('explore.html', title='Explore', posts=posts)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'POST':
        req_data = request.get_json()
        username = req_data['username']
        password = req_data['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return 'false'
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return 'true'
    else:
        return render_template('login.html', title='SignIn', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/users', methods=['GET', 'POST'])
def allUser():
    users = User.query.all()
    return render_template('alluser.html', users=users)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate():
            data = json.loads(request.form.get('objArr'))
            username = data[0].get('rname')
            email = data[0].get('remail')
            password = data[0].get('rpassword')
            password2 = data[0].get('rpassword2')
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return jsonify({'name': 'Yeah'})
        else:
            return jsonify({'error': form.errors,
                            'usernameError': form.username.errors,
                            'emailError': form.email.errors,
                            'passwordError': form.password.errors,
                            'password2Error': form.password2.errors})
    return render_template('register.html', title='Register', form=form)


@app.route('/validateUsername', methods=['GET', 'POST'])
def validate_username():
    username = request.json['username']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return "true"
    return "false"


@app.route('/validateEmail', methods=['GET', 'POST'])
def validate_email():
    email = request.json['email']
    user = User.query.filter_by(email=email).first()
    if user is None:
        return "true"
    return "false"


def save_profile_pics(raw_pic_filename):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(raw_pic_filename)
    pic_filename = random_hex + f_ext
    return pic_filename


@app.route('/edit-profile', methods=['GET', 'POST'])
@cross_origin()
@login_required
def user():
    form = UpdateProfileForm()
    if request.method == 'POST':
        file = request.files['picture']
        filename = secure_filename(file.filename)
        if filename:
            pic_filename = save_profile_pics(filename)
            pic_path = os.path.join(app.root_path, 'static/profile', pic_filename)
            file.save(pic_path)

            new_small_pic_size = (125, 125)
            img = Image.open(pic_path)
            img.thumbnail(new_small_pic_size)
            img.save(pic_path)
            current_user.image_file = pic_filename
        data = json.loads(request.form.get('objArr'))
        current_user.username = data[0].get('uname')
        current_user.email = data[0].get('uemail')
        current_user.about_me = data[0].get('uabout_me')
        db.session.commit()
        return jsonify({'error':  data[0].get('uname')})
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about_me.data = current_user.about_me
    image_file = url_for('static', filename='profile/' + current_user.image_file)

    return render_template('edit-profile.html', user=user, title="Account", image_file=image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    global pic_filename
    form = CreateNewPost()
    if request.method == 'POST':
        file = request.files['post_picture']
        filename = secure_filename(file.filename)
        if filename:
            pic_filename = save_profile_pics(filename)
            pic_path = os.path.join(app.root_path, 'static/post_pictures', pic_filename)
            file.save(pic_path)

            new_small_pic_size = (800, 600)
            img = Image.open(pic_path)
            img.thumbnail(new_small_pic_size)
            img.save(pic_path)
            Post.post_picture = pic_filename
            data = json.loads(request.form.get('objArr'))
            post = Post(title=data[0].get('p_title'), body=data[0].get('p_content'), post_picture=pic_filename, author=current_user)
            db.session.add(post)
            db.session.commit()
        else:
            data = json.loads(request.form.get('objArr'))
            post = Post(title=data[0].get('p_title'), body=data[0].get('p_content'), author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Posts have been created!', 'success')
    return render_template('create-posts.html', title='New Post', form=form, legend='New Post',
                           test1='new_post')


@app.route('/post/<string:post_id>/post-picture/display', methods=['GET', 'POST'])
@login_required
def post_picture_display(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('display-post-pictures.html', post=post)


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.path, Comment.timestamp.desc())

    post.comment_num = comments.count()
    db.session.commit()
    return render_template('post_itself.html', title="Post", post=post, comments=comments)


@app.route('/post/<int:post_id>/addComments', methods=['GET', 'POST'])
def addComments(post_id):
    form = AddComments()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        comment = Comment(text=form.content.data, post=post, c_author=current_user._get_current_object())
        comment.save()
        flash('Posts have been created!', 'success')
        return redirect(url_for('post', post_id=post.id))
    return render_template('addComments.html', title='Add Comments', form=form, legend='Add Comments', post=post)


@app.route('/post/<int:post_id>/comment/<int:comment_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_comment(post_id, comment_id):
    post = Post.query.get_or_404(post_id)
    d_comment = Comment.query.filter_by(id=comment_id).first()

    if request.method == 'POST':
        if post.author != current_user:
            abort(403)
        else:
             if d_comment.replies.first():
                for reply in d_comment.replies:
                    d_reply = Comment.query.filter_by(id=reply.id).first()
                    db.session.delete(d_reply)
                    db.session.commit()
                db.session.delete(d_comment)
                db.session.commit()
                return redirect(url_for('post', post_id=post.id))
             else:
                db.session.delete(d_comment)
                db.session.commit()
                return redirect(url_for('post', post_id=post.id))
    return render_template('delete-comment.html', post=post, comment=d_comment)


@app.route('/post/<string:post_id>/comment/<string:parent_id>/reply', methods=['GET', 'POST'])
def addReply(parent_id, post_id):
    post= Post.query.get_or_404(post_id)
    comment = Comment.query.get_or_404(parent_id)
    form = ReplyForm()
    if form.validate_on_submit():
        reply = Comment(text=form.content.data, post=post, c_author=current_user._get_current_object(), parent=comment)
        reply.save()
        return redirect(url_for('post', post_id=post.id))
    return render_template('addReply.html', title='Add Reply', form=form, legend='Add Reply', comment=comment, post=post)


@app.route('/post/<int:post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        if post.author != current_user:
            abort(403)
        db.session.delete(post)
        db.session.commit()
        flash('Posts have been deleted!', 'success')
        return redirect(url_for('home'))
    return render_template('delete-post.html', post=post)

def check_if_following(username):
    candidates = User.query.filter_by(username=username).first()

    if current_user.is_following(candidates):
        boolean = True
    else:
        boolean = False
    return boolean


@app.route('/user/<string:username>', methods=['POST', 'GET'])
@login_required
def user_posts(username):
    if request.method == 'POST':
        following_name = request.get_json()
        boolean = check_if_following(following_name)
        return jsonify({'error': boolean})
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).paginate(page=page, per_page=1000)
    return render_template('profile-dashboard.html', title='Users Posts', posts=posts, user=user)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect(url_for('home'))
    if user == current_user:
        return redirect(url_for('user_posts', username=username))
    current_user.follow(user)
    db.session.commit()
    return '', 204


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('home'))
    if user == current_user:
        return redirect(url_for('user_posts', username=username))
    current_user.unfollow(user)
    db.session.commit()
    return '', 204


@app.route('/post/<int:post_id>/like')
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    if post is None:
        flash('Post is not found')
        return redirect(url_for('home'))
    current_user.like_post(post)
    db.session.commit()
    num = post.likes.count()
    return jsonify({'error': num})


@app.route('/post/<int:post_id>/unlike')
@login_required
def unlike(post_id):
    post = Post.query.get_or_404(post_id)
    if post is None:
        flash('Post is not found')
        return redirect(url_for('home'))
    current_user.unlike_post(post)
    db.session.commit()
    num = post.likes.count()
    return jsonify({'name': num})


@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    what_to_search = g.search_form.q.data
    posts, total = Post.search(g.search_form.q.data, page,
                               10000)
    next_url = url_for("search", q=g.search_form.q.data, page=page + 1) \
        if total > page * 10000 else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url, what_to_search=what_to_search)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ResetPasswordRequestForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=request.form['email']).first()
            if user:
                send_password_reset_email(user)

    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('home'))
    return render_template('send_messages.html', legend='Send Message',
                           form=form, recipient=recipient)


@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.message_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
