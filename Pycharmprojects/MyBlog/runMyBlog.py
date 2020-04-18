from myBlogApp import app, db
from myBlogApp.models import User, Post, Notification, Comment, Message


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message, 'Notification': Notification, 'Comment': Comment}


app.run()
