from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    date_of_death = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<Author {self.id}: {self.name}>"

    def __str__(self):
        return f"{self.name} (Born: {self.birth_date}, Died: {self.date_of_death})"

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)

    author_id = db.Column(db.Integer, db.ForeignKey("author.id"), nullable=False)

    author = db.relationship("Author", backref=db.backref("books", lazy=True))

    def __repr__(self):
        return f"<Book {self.id}: {self.title}>"

    def __str__(self):
        return f"{self.title} ({self.publication_year})"