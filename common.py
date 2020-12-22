from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from flask import g
from datetime import datetime

def connectDB():
    global conn, paramsConn
    conn = connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
        'psgf', 'foodtracker', '127.0.0.1', 'ebaeba18'))
    conn.set_session(autocommit=True)
    return conn


def get_db():
    if not hasattr(g, 'pgdb'):
        g.pgdb = connectDB()
    return g.pgdb


def getDataFromDb(sql, values=None, cursor_factory=RealDictCursor):
    conn=get_db()
    cursor = conn.cursor(cursor_factory=cursor_factory)
    cursor.execute(sql,values)
    return cursor.fetchall()


def getValueFromDb(sql):
    rows = getDataFromDb(sql,cursor_factory=None)
    return None if len(rows) == 0 else rows[0][0]


def executeIUD(sql,values):
    conn=get_db()
    cursor = conn.cursor()
    cursor.execute(sql,values)
    conn.commit()
    cursor.close()

def closeDb():
    if hasattr(g,'pgdb'):
        g.pgdb.close()

def asPostgresDate(date):
    dt = datetime.strptime(date, '%Y-%m-%d')
    return datetime.strftime(dt, '%Y-%m-%d')
