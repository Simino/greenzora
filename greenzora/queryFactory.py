import sqlite3


def getCursor(db):
    connect = sqlite3.connect(db)
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    return cursor


def query(cursor, q):
    cursor.execute(q)
    return cursor.fetchall()
