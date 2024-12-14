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
            await cursor.close()
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
            await cursor.close()
    except Exception as e:
        print('Failed to get user roles:')
        print(e, user_id)

    try:
        return row[0].split(',')
    except Exception as e:
        return []

async def add_sr_role(role_name: str, role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO sr_role (role_name, role_id) VALUES (?, ?)', (role_name, role_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add SR role:')
        print(e, role_name, role_id)
        return False

async def remove_sr_role(role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('DELETE FROM sr_role WHERE role_id = ?', (role_id,))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to remove SR role:')
        print(e, role_id)
        return False

async def list_sr_roles():
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM sr_role')
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get SR roles:')
        print(e)
        return False

async def set_no_xp_role(role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('UPDATE no_xp_role SET role_id = ?', (role_id,))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to set No XP role:')
        print(e, role_id)
        return False

async def get_no_xp_role():
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM no_xp_role')
            row = await cursor.fetchone()
            await cursor.close()
        return row['role_id']
    except Exception as e:
        print('Failed to get SR roles:')
        print(e)
        return False

async def add_champion_role(role_name: str, role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO champion_role (role_name, role_id) VALUES (?, ?)', (role_name, role_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add champion role:')
        print(e, role_name, role_id)
        return False

async def remove_champion_role(role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('DELETE FROM champion_role WHERE role_id = ?', (role_id,))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to remove champion role:')
        print(e, role_id)
        return False

async def list_champion_roles():
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM champion_role')
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get champion roles:')
        print(e)
        return False

async def add_allowed_rank(role_name: str, role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('INSERT INTO allowed_rank (role_name, role_id) VALUES (?, ?)', (role_name, role_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add allowed rank role:')
        print(e, role_name, role_id)
        return False

async def remove_allowed_rank(role_id: int):
    try:
        async with aiosqlite.connect('db.db') as db:
            await db.execute('DELETE FROM allowed_rank WHERE role_id = ?', (role_id,))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to remove allowed rank role:')
        print(e, role_id)
        return False

async def list_allowed_ranks():
    try:
        async with aiosqlite.connect('db.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM allowed_rank')
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get allowed rank roles:')
        print(e)
        return False
