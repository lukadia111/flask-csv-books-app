Flask CSV Books App

A small Flask web app that imports a CSV file of books into an SQLite database and displays the records in a browser.

Features
- Upload a CSV file (title, author, year, genre, rating)
- Validates input (year and rating)
- Stores data in SQLite
- Browse/search the stored books
- View book details

How to run locally
1. Create and activate a virtual environment  
2. Install dependencies:
   pip install flask
3. Run the app:
   python app.py
4. Open in browser:
   http://127.0.0.1:5000
