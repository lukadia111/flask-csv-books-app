import csv
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "change-me"

DB_PATH = Path("books.db")
REQUIRED_COLUMNS = ["title", "author", "year", "genre", "rating"]
SORTABLE = ["title", "author", "year", "genre", "rating"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL,
            genre TEXT NOT NULL,
            rating REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def validate_row(row: dict) -> bool:
    # required fields
    for c in REQUIRED_COLUMNS:
        if c not in row or str(row[c]).strip() == "":
            return False
    # numeric fields
    try:
        year = int(row["year"])
        if year < 0 or year > 2100:
            return False
    except Exception:
        return False
    try:
        rating = float(row["rating"])
        if rating < 0 or rating > 5:
            return False
    except Exception:
        return False
    return True


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/import", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename.strip() == "":
            flash("Please choose a CSV file.", "error")
            return redirect(url_for("import_csv"))

        if not file.filename.lower().endswith(".csv"):
            flash("Only .csv files are allowed.", "error")
            return redirect(url_for("import_csv"))

        try:
            lines = file.stream.read().decode("utf-8", errors="replace").splitlines()
            reader = csv.DictReader(lines)

            headers = reader.fieldnames or []
            missing = [c for c in REQUIRED_COLUMNS if c not in headers]
            if missing:
                flash(f"Missing columns: {', '.join(missing)}", "error")
                return redirect(url_for("import_csv"))

            inserted = 0
            rejected = 0

            conn = get_db()
            for row in reader:
                if not validate_row(row):
                    rejected += 1
                    continue
                conn.execute(
                    "INSERT INTO books (title, author, year, genre, rating) VALUES (?, ?, ?, ?, ?)",
                    (row["title"].strip(), row["author"].strip(), int(row["year"]), row["genre"].strip(), float(row["rating"]))
                )
                inserted += 1
            conn.commit()
            conn.close()

            flash(f"Import done: {inserted} inserted, {rejected} rejected.", "success")
            return redirect(url_for("list_books"))

        except Exception as e:
            flash(f"Import failed: {e}", "error")
            return redirect(url_for("import_csv"))

    return render_template("import.html")


@app.get("/books")
def list_books():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "title").strip()
    order = request.args.get("order", "asc").strip().lower()

    if sort not in SORTABLE:
        sort = "title"
    if order not in ["asc", "desc"]:
        order = "asc"

    conn = get_db()
    params = []
    where = ""
    if q:
        where = "WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?"
        like = f"%{q}%"
        params = [like, like, like]

    rows = conn.execute(
        f"SELECT * FROM books {where} ORDER BY {sort} {order} LIMIT 50",
        params
    ).fetchall()
    conn.close()

    return render_template("list.html", rows=rows, q=q, sort=sort, order=order)


@app.get("/books/<int:book_id>")
def book_detail(book_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()

    if row is None:
        flash("Record not found.", "error")
        return redirect(url_for("list_books"))

    return render_template("detail.html", row=row)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
