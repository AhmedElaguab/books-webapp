import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from email_validator import validate_email, EmailNotValidError
from funtions import get_user_dict

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

    # if user is logged in, redicrect ot books page
    if "user" in session:
        return redirect(url_for("books"))

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    # if user is logged in, redicrect ot books page
    if "user" in session:
        return redirect(url_for("books"))

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


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login a user"""

    # if user is logged in, redicrect to books page
    if "user" in session:
        return redirect(url_for("books"))

    errors = {}

    # Check user login
    if request.method == "POST":

        # Get username
        username = request.form.get("username")

        # Get password
        password = request.form.get("password")

        # Get user
        user = db.execute(
            "SELECT * FROM users WHERE (username=:username OR email=:username)", {"username": username}).fetchone()

        # Validate the user input values
        if user is None:
            errors["username"] = "There is no user with this username"

        if user is not None and password != user[3]:
            errors["password"] = "The password is wrong"

        # Render login page with errors, when there is some error
        if errors.get("username") or errors.get("password"):
            return render_template("login.html", errors=errors)

        # If the user is registred, store it in session
        session["user"] = get_user_dict(user)

        # Redirect to books page
        return redirect(url_for("books"))

    return render_template("login.html", errors={})


@app.route("/books")
def books():
    """Books page."""

    # if user is logged in
    if "user" in session:
        books = []
        book_query = request.args.get("name")
        if book_query:
            # If, user enterd a search query
            book_query = book_query.strip()
            books = db.execute(
                "SELECT * FROM books WHERE (isbn LIKE :name OR title LIKE :name OR year LIKE :name OR author LIKE :name)", {"name": f"%{book_query}%"}).fetchall()

        return render_template("books.html", books=books)

    # If no user is logged in, redirect to login page
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user")

    return redirect(url_for("index"))


@app.route("/book/<string:isbn>")
def book(isbn):
    book = db.execute("SELECT * FROM books WHERE (isbn=:isbn)",
                      {"isbn": isbn}).first()
    return render_template("book.html", book=book)
