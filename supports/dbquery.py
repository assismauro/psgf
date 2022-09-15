from sqlalchemy import create_engine
import pandas as pd
import supports.app_object as app_object_support
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

def getEngine():
    return create_engine(app_object_support.app.config['SQLALCHEMY_DATABASE_URI'])


def getSession():
    session_factory = sessionmaker(getEngine())
    return scoped_session(session_factory)


def connectDB():
    engine = getEngine()
    return engine.connect()


def executeSQL(sql):
    conn = connectDB()
    try:
        return conn.execute(sql)
    except Exception as e:
        raise e


def getValueFromDb(sql):
    rows = executeSQL(sql)
    for row in rows:
        return row[0]
    return None

def getDictResultset(sql):
    return {row[0]: row[1] for row in executeSQL(sql)}


def getJSONResultset(sql):
    return executeSQL(sql).first()[0]


def getDataframeResultSet(sql):
    return pd.read_sql(sql, connectDB())

def tableExists(tablename, schema='public'):
    return getValueFromDb(f'''SELECT count(1) from (
   SELECT FROM information_schema.tables 
   WHERE  table_schema = '{schema}'
   AND    table_name   = '{tablename}'
   ) a''') == 1

def isAcessible(current_user, only_admin=False):
    try:
        if (current_user is None) or (not current_user.is_active()):
            return False
        else:
            if only_admin:
                if current_user.profile is None:
                    return False
                else:
                    return current_user.profile.is_administrator
            else:
                return True
    except:
        return False