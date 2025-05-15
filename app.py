from functools import wraps
import os
from flask import Flask, request, redirect, send_from_directory, url_for, render_template, flash
from models import *
from config import Config
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

# Initializing objects in flask application context
db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get_or_404(int(user_id))

# CREATE ADMIN
def create_librarian():
    existing_librarian = User.query.filter_by(librarian = True).first()
    if existing_librarian:
        return
    new_librarian = User(
                        name="librarian",
                        email="librarian@library.com",
                        password="1"
                        )
    new_librarian.librarian = True
    db.session.add(new_librarian)
    db.session.commit()
    return "Librarian created"

# Creating tables
with app.app_context():
    db.create_all()
    create_librarian()

def librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the current user is a librarian
        if not current_user.librarian:
            flash("You must be a librarian to access this page", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function



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


######################################################
################## CRUD on SECTIONS ##################
######################################################

@app.route("/sections/create", methods=["GET", "POST"])
@login_required
@librarian_required
def create_section():
    if request.method == "POST":
        # Retrieve form data
        name = request.form["name"]
        description = request.form["description"]

        # Create a new section
        section = Section(name=name, description=description)

        # Add the section to the database
        db.session.add(section)
        db.session.commit()

        flash("Section created successfully!", "success")
        return redirect(url_for("list_sections"))

    return render_template("sections/create.html")

@app.route("/sections")
@login_required
def list_sections():
    query = request.args.get("search", "")
    if query:
        sections = Section.query.filter(Section.name.ilike(f"%{query}%")).all()
    else:
        sections = Section.query.all()
    return render_template("sections/list.html", sections=sections, query=query)


@app.route("/sections/<int:section_id>/edit", methods=["GET", "POST"])
@login_required
@librarian_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)

    if request.method == "POST":
        # Retrieve form data
        section.name = request.form["name"]
        section.description = request.form["description"]

        print( request.form["description"])

        # Update the section in the database
        db.session.commit()

        flash("Section updated successfully!", "success")
        return redirect(url_for("list_sections"))

    return render_template("sections/edit.html", section=section)


@app.route("/sections/<int:section_id>/delete", methods=["POST"])
@login_required
@librarian_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)

    # Delete the section from the database
    db.session.delete(section)
    db.session.commit()

    flash("Section deleted successfully!", "success")
    return redirect(url_for("list_sections"))

###################################################################
################## CRUD on BOOKS ##################################
###################################################################

@app.route("/books/create", methods=["GET", "POST"])
@login_required
@librarian_required
def create_book():
    sections = Section.query.all()
    if request.method == "POST":
        # Retrieve form data
        name = request.form["name"]
        author = request.form["author"]
        content = request.form["content"]
        section_id = request.form["section_id"]

        pdf_file = request.files.get("pdf_file")
        pdf_path = None

        if pdf_file and pdf_file.filename != "":
            filename = secure_filename(name)
            pdf_path = filename
            os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"]), exist_ok=True)
            pdf_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        book = Book(name=name, author=author, content=content, section_id=section_id, pdf_path=pdf_path)

        # Add the book to the database
        db.session.add(book)
        db.session.commit()

        flash("Book created successfully!", "success")
        return redirect(url_for("list_books"))
    return render_template("books/create.html", sections= sections)

@app.route("/books")
@login_required
def list_books():
    query = request.args.get("search", "")
    author = request.args.get("author", "")
    section_id = request.args.get("section_id", "")

    books_query = Book.query

    if query:
        books_query = books_query.filter(Book.name.ilike(f"%{query}%"))
    if author:
        books_query = books_query.filter(Book.author.ilike(f"%{author}%"))
    if section_id:
        books_query = books_query.filter(Book.section_id == section_id)

    books = books_query.all()
    
    sections = Section.query.all()
    authors = [book.author for book in Book.query.distinct(Book.author).all()]

    return render_template("books/list.html", books=books, query=query, author=author, section_id=section_id,
                           sections=sections, authors=authors)

@app.route('/uploads/<path:filename>')
@login_required
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
@librarian_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    sections = Section.query.all()
    if request.method == "POST":
        book.name = request.form["name"]
        book.content = request.form["content"]
        book.author = request.form["author"]
        book.section_id = request.form["section_id"]
        db.session.commit()
        flash("Book updated successfully.", "success")
        return redirect(url_for("list_books"))
    return render_template("books/edit.html", book=book, sections=sections)

@app.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
@librarian_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully.", "success")
    return redirect(url_for("list_books"))

if __name__ == "__main__":
    app.run(debug=True)