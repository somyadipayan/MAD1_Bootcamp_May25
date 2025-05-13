from flask import Flask, request, redirect, url_for, render_template, flash
from models import *
from config import Config
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.config.from_object(Config)

# Initializing objects in flask application context
db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# CREATE ADMIN
def create_librarian():
    existing_librarian = User.query.filter_by(librarian = True).first()
    if existing_librarian:
        return
    new_librarian = User(
                        name="librarian",
                        email="librarian@library.com",
                        password=bcrypt.generate_password_hash("1").decode("utf-8")
                        )
    new_librarian.librarian = True
    db.session.add(new_librarian)
    db.session.commit()
    return "Librarian created"

# Creating tables
with app.app_context():
    db.create_all()
    create_librarian()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Retrieve form data
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()

        if not existing_user:
            # Create a new user
            user = User(name=name, email=email, password=password)
            
            # Add the user to the database
            db.session.add(user)
            db.session.commit()

            flash("User registered successfully!", "success")
            return redirect(url_for("login"))
        else:
            flash("User already exists!", "error")
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Retrieve form data
        email = request.form["email"]
        password = request.form["password"]
        
        # Query the database for the user
        user = User.query.filter_by(email=email).first()

        # if email exists and password matches
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

