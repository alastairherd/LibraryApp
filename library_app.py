from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sqlite3
import isbnlib
import requests
import sys

# Initialize SQLite database
conn = sqlite3.connect("books.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS books
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 isbn TEXT UNIQUE,
                 title TEXT,
                 author TEXT,
                 cover BLOB)''')


# Function to fetch and save ISBN data
def fetch_and_save_isbn():
    isbn = isbn_input.text()
    try:
        result_label.setText("Reading ISBN.")
        QApplication.processEvents()
        book = isbnlib.meta(isbn)
        title = book.get("Title")
        author = book.get("Authors")[0]
        cover_info = isbnlib.cover(isbn)
        cover_url = cover_info.get("thumbnail")

        # Fetch and store the cover image
        response = requests.get(cover_url)
        cover_blob = response.content
        # Use a parameterized query to insert the binary data
        cursor.execute(
            """
            INSERT INTO books
                (isbn, title, author, cover)
            VALUES
                (?, ?, ?, ?)
            """,
            (isbn, title, author, sqlite3.Binary(cover_blob)),
        )
        conn.commit()

        # Display the cover image
        pixmap = QPixmap()
        pixmap.loadFromData(cover_blob)
        cover_label.setPixmap(pixmap)

        result_label.setText("Saved.")
        view_db()
    except isbnlib.NotValidISBNError:
        result_label.setText("Invalid ISBN.")
        view_db()
    except sqlite3.IntegrityError:
        result_label.setText("ISBN Already in Database.")
        view_db()
    except TypeError:
        result_label.setText("Please write a ISBN.")
        view_db()
    # except:
    #     result_label.setText("Error.")


def view_db():
    cursor.execute("SELECT isbn, title, author, cover FROM books")
    rows = cursor.fetchall()
    tableWidget.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, val in enumerate(row[:-1]):  # Exclude the last column (cover)
            tableWidget.setItem(i, j, QTableWidgetItem(str(val)))


def initial_display():
    cursor.execute("SELECT cover FROM books ORDER BY id DESC LIMIT 1")
    cover_blob = cursor.fetchone()[0]
    if cover_blob:
        pixmap = QPixmap()
        pixmap.loadFromData(cover_blob)
        cover_label.setPixmap(pixmap)


def display_selected_cover(item):
    row = item.row()
    cursor.execute("SELECT cover FROM books LIMIT 1 OFFSET ?", (row,))
    cover_blob = cursor.fetchone()[0]
    if cover_blob:
        pixmap = QPixmap()
        pixmap.loadFromData(cover_blob)
        cover_label.setPixmap(pixmap)


# Initialize PyQt5 App
app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()

isbn_input = QLineEdit()
isbn_input.setPlaceholderText("Enter ISBN")
layout.addWidget(isbn_input)

fetch_button = QPushButton("Fetch and Save")
fetch_button.clicked.connect(fetch_and_save_isbn)
layout.addWidget(fetch_button)

# view_button = QPushButton("View Database")
# view_button.clicked.connect(view_db)
# layout.addWidget(view_button)

result_label = QLabel("")
result_label.setAlignment(Qt.AlignCenter)
layout.addWidget(result_label)

cover_label = QLabel()
layout.addWidget(cover_label)

tableWidget = QTableWidget()
tableWidget.setColumnCount(3)
tableWidget.setHorizontalHeaderLabels(["ISBN", "Title", "Author"])
tableWidget.itemClicked.connect(display_selected_cover)
layout.addWidget(tableWidget)
view_db()

try:
    initial_display()
except IndexError:
    pass

window.setLayout(layout)
window.show()

sys.exit(app.exec_())
