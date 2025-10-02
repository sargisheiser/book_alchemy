import os
from flask import redirect, url_for, flash
from flask import Flask, render_template, request
from datetime import datetime
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


@app.route("/")
def home():
    sort_by = request.args.get("sort", "title")
    search = request.args.get("search", None)

    query = Book.query.join(Author)

    if search:
        query = query.filter(
            (Book.title.ilike(f"%{search}%")) |
            (Author.name.ilike(f"%{search}%"))
        )

    if sort_by == "author":
        books = query.order_by(Author.name).all()
    else:
        books = query.order_by(Book.title).all()

    return render_template("home.html", books=books, search=search)


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if request.method == "POST":
        name = request.form.get("name")
        birth_date_str = request.form.get("birth_date")
        death_date_str = request.form.get("date_of_death")

        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date() if birth_date_str else None
        date_of_death = datetime.strptime(death_date_str, "%Y-%m-%d").date() if death_date_str else None

        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
        db.session.add(new_author)
        db.session.commit()

        message = f"Author '{name}' added successfully!"
        return render_template("add_author.html", message=message)

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    authors = Author.query.order_by(Author.name).all()

    if request.method == "POST":
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        publication_year = request.form.get("publication_year")
        author_id = request.form.get("author_id")
        rating = request.form.get("rating") or None

        if rating:
            rating = int(rating)

        new_book = Book(
            isbn=isbn,
            title=title,
            publication_year=publication_year,
            author_id=author_id,
            rating=rating
        )
        db.session.add(new_book)
        db.session.commit()

        message = f"Book '{title}' added successfully!"
        return render_template("add_book.html", authors=authors, message=message)

    return render_template("add_book.html", authors=authors)


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author = book.author

    db.session.delete(book)
    db.session.commit()

    if not author.books:
        db.session.delete(author)
        db.session.commit()
        flash(f"Book '{book.title}' and author '{author.name}' were deleted.", "success")
    else:
        flash(f"Book '{book.title}' was deleted.", "success")

    return redirect(url_for("home"))


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == "POST":
        rating = request.form.get("rating")
        if rating:
            book.rating = int(rating)
            db.session.commit()
            flash(f"Rating for '{book.title}' updated to {book.rating}/10", "success")
        return redirect(url_for("book_detail", book_id=book.id))

    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id):
    author = Author.query.get_or_404(author_id)
    return render_template("author_detail.html", author=author)


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)

    db.session.delete(author)
    db.session.commit()

    flash(f"Author '{author.name}' and all their books were deleted.", "success")
    return redirect(url_for("home"))


@app.route("/recommendations")
def recommendations():
    books = Book.query.order_by(Book.rating.desc().nullslast(), Book.title).limit(5).all()

    if not books:
        flash("No books available for recommendations. Add some first!", "info")

    return render_template("recommendations.html", books=books)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
