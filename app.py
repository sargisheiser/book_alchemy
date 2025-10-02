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


       new_book = Book(
           isbn=isbn,
           title=title,
           publication_year=publication_year,
           author_id=author_id,
       )
       db.session.add(new_book)
       db.session.commit()


       message = f" Book '{title}' added successfully!"
       return render_template("add_book.html", authors=authors, message=message)

   return render_template("add_book.html", authors=authors)

@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author = book.author  # store reference for later

    db.session.delete(book)
    db.session.commit()

    if not author.books:
        db.session.delete(author)
        db.session.commit()
        flash(f"Book '{book.title}' and author '{author.name}' were deleted.", "success")
    else:
        flash(f"Book '{book.title}' was deleted.", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":
   with app.app_context():
       db.create_all()
   app.run(debug=True)