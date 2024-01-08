import sqlite3
import uuid

def open_db():
    return sqlite3.connect('db.db')

def execute(*args):
    conn = open_db()
    cur = conn.cursor()
    cur.execute(*args)
    if args[0].lower().startswith('select'):
        results = cur.fetchall()
    else:
        conn.commit()
    conn.close()

    try:
        return results
    except: pass

def add_user(user_id: int, roles: str):
    try:
        execute('INSERT INTO inventory (id, user_id, roles) VALUES (?, ?, ?)', (str(uuid.uuid4()), user_id, roles))
        return True
    except Exception as e:
        print('Failed to add user!')
        print(e)
        print(user_id)
        print(roles)
        return False

def update_user(user_id, roles):
    try:
        execute('UPDATE inventory SET roles = ? WHERE user_id = ?', (roles, user_id))
        return True
    except Exception as e:
        print('Failed to update user!')
        print(e)
        print(user_id)
        print(roles)
        return False

def check_user(user_id):
    if execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,)):
        return True
    return False

def get_roles(user_id):
    conn = open_db()
    cur = conn.cursor()
    cur.execute('SELECT roles FROM inventory WHERE user_id = ?', (user_id,))

    try:
        roles = cur.fetchone()[0]
        conn.close()
        return roles.split(',')
    except Exception as e:
        conn.close()
        return []

def save_slot_pull(user_id, datestamp):
    try:
        execute('INSERT INTO gamba (id, user_id, datestamp) VALUES (?, ?, ?)', (str(uuid.uuid4()), user_id, datestamp))
        return True
    except Exception as e:
        print('Failed to add gamba!')
        print(e)
        print(user_id)
        print(datestamp)
        return False

def get_last_slot_pull(user_id):
    conn = open_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM gamba WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()

    try:
        return {
            "id":        row[0],
            "user_id":   row[1],
            "datestamp": row[2]
        }
    except:
        return None
