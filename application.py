import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    errors = {"email": None, "username": None, "password": None}

    # Check if the method is post
    if request.method == "POST":
        # Validate email input value
        email = request.form.get("email")
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            errors["email"] = e

        # Validate username input values
        username = request.form.get("username").strip()
        if len(username) < 3:
            errors["username"] = "The username is not valid. It must be at least 3 characters."

        # Validate password input values
        password = request.form.get("password").strip()
        if len(password) < 3:
            errors["password"] = "The password is not valid. It must be at least 3 characters."

        # Check that there is no user with the same email or username
        users = db.execute("SELECT email, username FROM users WHERE  email=:email OR username=:username", {
            "email": email, "username": username}).fetchall()

        for user in users:
            if user is not None:
                if user[0] == email:
                    errors["email"] = "The email is not valid. It was used before."
                if user[1] == username:
                    errors["username"] = "The username is not valid. It was used before."

        # Return registration page with error messages
        if errors["email"] or errors["username"] or errors["password"]:
            return render_template("register.html", errors=errors)

        # Insert data into database
        db.execute("INSERT INTO users (email, username, password) VALUES (:email, :username, :password)", {
            "email": email, "username": username, "password": password,
        })
        db.commit()

        # Render registration success message
        return render_template("register_success.html")

    # Return registration page for get requests
    return render_template("register.html", errors=errors)
