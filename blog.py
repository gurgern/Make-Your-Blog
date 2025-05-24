from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash
from edit_db import User

app = Flask(__name__)
app.secret_key = "your_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"



def close_db(conn=None):
    if conn is not None:
        conn.close()


@app.teardown_appcontext
def close_connection(exception):
    close_db()


@app.route("/")
def index():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute(''' SELECT info.id, info.title, info.content, info.author_id,
                       user.username, COUNT(like.id) AS likes FROM info
                       JOIN user ON info.author_id = user.id
                       LEFT JOIN like ON info.id = like.post_id
                       GROUP BY info.id, info.title, info.content,
                       info.author_id, user.username ''')
    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        posts.append({"id": post[0], "title": post[1], "content": post[2],
                    "author_id": post[3], "username": post[4], "likes": post[5]})
        if current_user.is_authenticated:
            cursor.execute(
                "SELECT post_id FROM like WHERE user_id = ?", (current_user.id, )
            )
            likes_result = cursor.fetchall()
            liked_posts = []
            for like in likes_result:
                liked_posts.append(like[0])
            posts[-1]["liked_posts"] = liked_posts
    context = {"posts": posts}
    return render_template("blog.html", **context)


@app.route("/register/", methods=["GET", "POST"])
def register():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    if request.method == "POST":
        print(request.form)
        username = request.form["Username"]
        password = request.form["Password"]
        print(username)
        try:
            print(11)
            cursor.execute("INSERT INTO user (username, password_hash) VALUES (?,?)",(username, generate_password_hash(password)))
            conn.commit()
            print("registration successful")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            return render_template("register.html",
                               message="Username already exists")
    return render_template("register.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    if request.method == "POST":
        username = request.form["Username"]
        password = request.form["Password"]
        user = cursor.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if user and User(user[0], user[1], user[2]).check_password(password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for("index"))
        else:
            return render_template("login.html",
                               message="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/add/", methods=["GET", "POST"])
@login_required
def add_post():
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = request.form["date"]
        cursor.execute(
            "INSERT INTO info (title, content, date, author_id) VALUES (?, ?, ?, ?)",
            (title, content, date, current_user.id)
        )
        conn.commit()
        return redirect(url_for("index"))
    return render_template("add_blog.html")


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    print(post_id)
    post = cursor.execute("SELECT * FROM info WHERE id = ?",
                                        (post_id,)).fetchone()
    if post and post[5] == current_user.id:
        cursor.execute("DELETE FROM info WHERE id = ?", (post_id,))
        conn.commit()
        print(post_id)
        return redirect(url_for("index"))
    else :
        print(post[5])
        return redirect(url_for("login"))


def user_is_liking(user_id, post_id):
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    like = cursor.execute(
        "SELECT * FROM like WHERE user_id = ? AND post_id = ?",
        (user_id, post_id)).fetchone()
    return bool(like)

@app.route("/like/<int:post_id>")
@login_required
def like_post(post_id):
    print("test")
    connection = sqlite3.connect("test.db")
    cursor = connection.cursor()
    post = cursor.execute("SELECT * FROM info WHERE id = ?",
                          (post_id,)).fetchone()
    if post:
        print("test")
        if user_is_liking(current_user.id, post_id):
            cursor.execute(
                "DELETE FROM like WHERE user_id = ? AND post_id = ?",
                (current_user.id, post_id))
            connection.commit()
            print("you unliked this post")
        else:
            cursor.execute(
                "INSERT INTO like (user_id, post_id) VALUES (?, ?)",
                (current_user.id,post_id))
            connection.commit()
            print("you liked this post")
        return redirect(url_for("index"))
    return "Post not found", 404



@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user:
        return User(user[0], user[1], user[2])
    return None


if __name__ == "__main__":
    app.run()