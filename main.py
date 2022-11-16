import os
import smtplib
import time
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, FileField, SubmitField, EmailField, PasswordField, Label
from wtforms.validators import DataRequired, Email, Length

blog_image = "../static/img/post-sample-image.jpg"
my_email = os.environ['my_mail']
pwd = os.environ['pwd']


def create_app():
    app_in = Flask(__name__)
    Bootstrap(app_in)
    return app_in


today_date = time.strftime("%B, %d %Y")
db_url = "sqlite:///blogs.db"
UPLOAD_FOLDER = r'static/upload_images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
app = create_app()
ckeditor = CKEditor(app)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SECRET_KEY'] = os.urandom(32)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)
login_manager = LoginManager(app=app)
login_manager.login_message = "Log in is required before this action."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):
    __tablename__ = "User_table"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    posts = db.relationship("Post", back_populates="author_rel")
    comments = db.relationship("Comment", back_populates="author_rel")


class Post(db.Model):
    __tablename__ = "Post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    subtitle = db.Column(db.String(50), nullable=False)
    img_url = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(2500), nullable=False)
    author = db.Column(db.Integer, db.ForeignKey("User_table.id"))
    author_rel = db.relationship("User", back_populates="posts")
    date = db.Column(db.String(20), nullable=False)
    comments = db.relationship("Comment", back_populates="post_rel")


class Comment(db.Model):
    __tablename__ = "Comment"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("User_table.id"))
    author_rel = db.relationship("User", back_populates="comments")
    post = db.Column(db.Integer, db.ForeignKey("Post.id"))
    post_rel = db.relationship("Post", back_populates="comments")
    body = db.Column(db.String(1500), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)


class PostForm(FlaskForm):
    title = StringField(label="Title:", validators=[DataRequired(message="Insert title")])
    subtitle = StringField(label="Subtitle:", validators=[DataRequired(message="Insert subtitle")])
    img = FileField(label="Blog display picture:", validators=[DataRequired(message="Upload image.")])
    body = CKEditorField(label="Write a blog:", validators=[DataRequired(message="write a blog.")])
    # author = StringField(label="Author:", validators=[DataRequired(message="Add writer name.")])
    # date = DateField(label="Published on:", validators=[DataRequired(message="Published on.")])
    submit = SubmitField(label="Publish")


class Register(FlaskForm):
    name = StringField(label="Name:", validators=[DataRequired(message="Insert name")])
    email = EmailField(label="Email:", validators=[DataRequired(message="Enter email"), Email(message="Invalid Email")])
    password = PasswordField(label="Password:", validators=[DataRequired(message="Enter password"),
                                                            Length(min=8, message="Password is too short")])
    sign_up = SubmitField(label="SIGN UP")


class CommentForm(FlaskForm):
    body = CKEditorField(label="Add comment", validators=[DataRequired(message="Add comment then submit.")])
    submit = SubmitField(label="Post")


def admin_only(function):
    @wraps(function)
    def wrapper():
        if not current_user.is_anonymous:
            if current_user.email == "mdvankar1990@gmail.com":
                return function()
            return "not allowed"
        return "no such user."

    return wrapper


@app.route('/')
def home():
    today_time = time.strftime("%I:%M:%S")
    db.create_all()
    data = db.session.query(Post).all()
    return render_template("index.html", data=data, time=today_time, date=today_date)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    today_time = time.strftime("%I:%M:%S")
    register_form = Register()
    if register_form.validate_on_submit():
        new_user = User()
        new_user.email = request.form['email']
        if User.query.filter_by(email=request.form['email']).first() is None:
            new_user.name = request.form['name']
            new_user.password = generate_password_hash(request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        flash("Your email is already registered.Log in here!")
        return redirect(url_for('login'))

    return render_template('register.html', login_form=register_form, time=today_time, date=today_date)


@app.route("/login", methods=['GET', 'POST'])
def login():
    today_time = time.strftime("%I:%M:%S")
    login_form = Register()
    login_form.sign_up.label = Label(field_id="sign_up", text="Log in")
    if login_form.validate_on_submit() and request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        current = User.query.filter_by(email=email).first()
        if current is not None:
            if check_password_hash(current.password, password):
                load_user(current.id)
                login_user(current)
                return redirect(url_for('home'))
            flash("Wrong Password.")
            return render_template('register.html', login_form=login_form, time=today_time, date=today_date)
        flash("No such user exist.")
        return render_template('register.html', login_form=login_form, time=today_time, date=today_date)
    return render_template('register.html', login_form=login_form, time=today_time, date=today_date)


@app.route("/post/<int:id>", methods=['GET', 'POST'])
def get_blog(id):
    today_time = time.strftime("%I:%M:%S")
    blog = Post.query.get(id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit() and request.method == "POST":
        comment = Comment()
        comment.body = request.form['body']
        if not current_user.is_anonymous:
            comment.author = current_user.id
            comment.post = id
            comment.time = today_time
            comment.date = today_date
            db.session.add(comment)
            db.session.commit()
            return render_template("post.html", form=comment_form, data=blog, time=today_time, date=today_date)
        flash("Log in before commenting.")
        return redirect(url_for("login"))
    return render_template("post.html", form=comment_form, data=blog, time=today_time, date=today_date)


@app.route('/about')
def about():
    today_time = time.strftime("%I:%M:%S")
    return render_template("about.html", time=today_time, date=today_date)


@app.route('/contact')
def contact():
    today_time = time.strftime("%I:%M:%S")
    return render_template("contact.html", time=today_time, date=today_date)


@app.route('/formentry', methods=['POST'])
def receive_data():
    print(my_email)
    print(pwd)
    today_time = time.strftime("%I:%M:%S")
    if request.method == "POST":
        connection = smtplib.SMTP("SMTP.GMAIL.COM", port=587)
        connection.starttls()
        connection.login(my_email, pwd)
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        message_to_send = f"Subject:Customer details\n\nCustomer name: {name}-\nEmail:{email}\nPhone:{phone}\n" \
                          f"message:{message}"
        connection.sendmail(from_addr=my_email, to_addrs=my_email, msg=message_to_send)
        connection.close()
        flash(message="We received your info.Get back to you soon.")
        return redirect(url_for("contact"))

    return redirect(url_for("contact"))


@app.route("/delete/<int:id>", methods=['GET'])
@login_required
def delete(id):
    post_to_update = Post.query.get(id)
    if current_user.id == post_to_update.author:
        db.session.delete(post_to_update)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    today_time = time.strftime("%I:%M:%S")
    post_edit = Post.query.get(id)
    if current_user.id == post_edit.author:
        form_edit = PostForm(obj=post_edit)
        if form_edit.validate_on_submit() and request.method == "POST":
            post_edit.title = request.form['title']
            post_edit.subtitle = request.form['subtitle']
            post_edit.body = request.form['body']
            file = request.files['img']
            if file.filename == "":
                return redirect(url_for('edit', id=id))
            if file.filename.split(".")[1] in ALLOWED_EXTENSIONS:
                upload_path = UPLOAD_FOLDER + "/" + file.filename
                file.save(dst=upload_path)
                try:
                    os.remove(path="static/upload_images/206368.jpg")
                except FileNotFoundError:
                    pass
                img_url = "../" + upload_path
                post_edit.img_url = img_url
                db.session.commit()
                file.close()
                return redirect(url_for('get_blog', id=id))

        return render_template("add.html", form=form_edit, id=id, time=today_time, date=today_date)
    return redirect(url_for('get_blog', id=id))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    today_time = time.strftime("%I:%M:%S")
    form = PostForm()
    if request.method == 'POST' and form.validate_on_submit():
        title = request.form['title']
        subtitle = request.form['subtitle']
        body = request.form['body']
        date = today_date
        author = current_user.id
        file = request.files['img']
        if file.filename == "":
            return render_template('add.html', id=0, form=form, date=today_date)
        if file.filename.split(".")[1] in ALLOWED_EXTENSIONS:
            upload_path = UPLOAD_FOLDER + "/" + file.filename
            file.save(dst=upload_path)
            img_url = "../" + upload_path
            new_blog = Post(title=title, subtitle=subtitle, body=body, author=author, date=date, img_url=img_url)
            db.session.add(new_blog)
            db.session.commit()
            file.close()
            return redirect(url_for('home'))

    return render_template('add.html', id=0, form=form, time=today_time, date=today_date)


@app.route("/admin")
@admin_only
def admin_page():
    return "<p>mohan</p>"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
