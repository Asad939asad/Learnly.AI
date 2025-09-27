import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'books.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create books table
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_book(title, file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO books (title, file_path) VALUES (?, ?)', (title, file_path))
    book_id = c.lastrowid
    conn.commit()
    conn.close()
    return book_id

def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, title, file_path, upload_date FROM books ORDER BY upload_date DESC')
    books = c.fetchall()
    conn.close()
    return [{'id': b[0], 'title': b[1], 'file_path': b[2], 'upload_date': b[3]} for b in books]

def get_book_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, title, file_path, upload_date FROM books WHERE id = ?', (book_id,))
    book = c.fetchone()
    conn.close()
    return book and {'id': book[0], 'title': book[1], 'file_path': book[2], 'upload_date': book[3]}
