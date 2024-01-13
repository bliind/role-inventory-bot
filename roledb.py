import aiosqlite
import uuid

async def add_user(user_id: int, roles: str):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO inventory (id, user_id, roles) VALUES (?, ?, ?)', (str(uuid.uuid4()), user_id, roles))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to save user roles:')
        print(e, user_id, roles)
        return False

async def update_user(user_id: int, roles: str):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('UPDATE inventory SET roles = ? WHERE user_id = ?', (roles, user_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to update user roles:')
        print(e, user_id, roles)
        return False

async def check_user(user_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            cursor = await db.execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
        if row:
            return True
        else:
            return False
    except Exception as e:
        print('Failed to check user exists:')
        print(e, user_id)
        return False

async def get_roles(user_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            cursor = await db.execute('SELECT roles FROM inventory WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
    except Exception as e:
        print('Failed to get user roles:')
        print(e, user_id)

    try:
        return row[0].split(',')
    except Exception as e:
        return []
