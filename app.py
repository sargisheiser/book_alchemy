import os
import re
from flask import redirect, url_for, flash, Flask, render_template, request
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from data_models import db, Author, Book

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    template_folder=os.path.join(os.path.dirname(__file__), "templates")
)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "my-secret-key"

db.init_app(app)


def validate_isbn(isbn):
    """Validate ISBN (basic check for 10 or 13 digits, optionally with dashes)."""
    if not isbn:
        return False
    pattern = r"^(97(8|9))?\d{9}(\d|X)$"
    return bool(re.match(pattern, isbn.replace("-", "").strip()))


def sanitize_input(value):
    """Trim whitespace and ensure safe query behavior."""
    return value.strip() if value else ""


@app.route("/")
def home():
    """Home page: shows all books with sorting and search."""
    sort_by = request.args.get("sort", "title")
    search = sanitize_input(request.args.get("search", ""))

    query = Book.query.join(Author)

    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%")) |
            (Author.name.ilike(f"%{search}%"))
        )

    books = (
        query.order_by(Author.name if sort_by == "author" else Book.title)
        .all()
    )

    return render_template("home.html", books=books, search=search)


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """Add a new author with input validation and error handling."""
    if request.method == "POST":
        name = sanitize_input(request.form.get("name"))
        birth_date_str = sanitize_input(request.form.get("birth_date"))
        death_date_str = sanitize_input(request.form.get("date_of_death"))

        if not name:
            flash("Author name cannot be empty.", "danger")
            return render_template("add_author.html")

        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date() if birth_date_str else None
            date_of_death = datetime.strptime(death_date_str, "%Y-%m-%d").date() if death_date_str else None

            new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
            db.session.add(new_author)
            db.session.commit()

            flash(f"Author '{name}' added successfully!", "success")
            return redirect(url_for("home"))

        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}", "danger")

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """Add a new book with validation and safe commit."""
    authors = Author.query.order_by(Author.name).all()

    if request.method == "POST":
        isbn = sanitize_input(request.form.get("isbn"))
        title = sanitize_input(request.form.get("title"))
        publication_year = sanitize_input(request.form.get("publication_year"))
        author_id = request.form.get("author_id")
        rating = request.form.get("rating")

        if not title or not author_id:
            flash("Title and author are required fields.", "danger")
            return render_template("add_book.html", authors=authors)

        if isbn and not validate_isbn(isbn):
            flash("Invalid ISBN format. Please provide a valid ISBN-10 or ISBN-13.", "danger")
            return render_template("add_book.html", authors=authors)

        try:
            rating = int(rating) if rating else None
            new_book = Book(
                isbn=isbn or None,
                title=title,
                publication_year=publication_year or None,
                author_id=author_id,
                rating=rating
            )
            db.session.add(new_book)
            db.session.commit()

            flash(f"Book '{title}' added successfully!", "success")
            return redirect(url_for("home"))

        except ValueError:
            flash("Invalid input for rating or publication year.", "danger")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}", "danger")

    return render_template("add_book.html", authors=authors)


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """Delete a book, and if author has no remaining books, delete author too."""
    book = Book.query.get(book_id)
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    author = book.author

    try:
        db.session.delete(book)
        db.session.commit()

        if not author.books:
            db.session.delete(author)
            db.session.commit()
            flash(f"Book '{book.title}' and author '{author.name}' were deleted.", "success")
        else:
            flash(f"Book '{book.title}' was deleted.", "success")

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Error deleting book: {str(e)}", "danger")

    return redirect(url_for("home"))


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_detail(book_id):
    """View or update book details (e.g., rating)."""
    book = Book.query.get_or_404(book_id)

    if request.method == "POST":
        rating = request.form.get("rating")
        try:
            if rating:
                book.rating = int(rating)
                db.session.commit()
                flash(f"Rating for '{book.title}' updated to {book.rating}/10", "success")
        except (ValueError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(f"Error updating rating: {str(e)}", "danger")

        return redirect(url_for("book_detail", book_id=book.id))

    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id):
    """Display author details."""
    author = Author.query.get_or_404(author_id)
    return render_template("author_detail.html", author=author)


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    """Delete an author and all their books."""
    author = Author.query.get(author_id)
    if not author:
        flash("Author not found.", "danger")
        return redirect(url_for("home"))

    try:
        db.session.delete(author)
        db.session.commit()
        flash(f"Author '{author.name}' and all their books were deleted.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Error deleting author: {str(e)}", "danger")

    return redirect(url_for("home"))


@app.route("/recommendations")
def recommendations():
    """Display top-rated book recommendations."""
    try:
        books = Book.query.order_by(Book.rating.desc().nullslast(), Book.title).limit(5).all()
        if not books:
            flash("No books available for recommendations. Add some first!", "info")
    except SQLAlchemyError as e:
        flash(f"Error loading recommendations: {str(e)}", "danger")
        books = []

    return render_template("recommendations.html", books=books)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
