"""View database data from your terminal"""
import sqlite3

def view():
    db_connection = sqlite3.connect('social.db')
    db_cursor = db_connection.cursor()
    db_cursor.execute("SELECT * FROM User")
    # db_cursor.execute("SELECT * FROM Post")
    # db_cursor.execute("SELECT * FROM Relationship")
    rows = db_cursor.fetchall()
    db_connection.close()
    return rows


print(view())
