import sqlite3

from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"

login_manager = LoginManager(app)
login_manager.login_view = "login"

conn = sqlite3.connect("test.db", check_same_thread=False)
cursor = conn.cursor()


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute(
        "SELECT * FROM user WHERE id = ?", (user_id)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None



# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS user(
# 	id INTEGER PRIMARY KEY AUTOINCREMENT,
# 	username TEXT UNIQUE NOT NULL,
# 	password_hash TEXT NOT NULL
# );
# """)
#
#
# cursor.execute("ALTER TABLE info ADD autor_id INTEGER;")

# cursor.execute("INSERT INTO USER VALUES (?,?,?)",
#                (1, "GURGERN", generate_password_hash("qwerty234")))

conn.commit()
