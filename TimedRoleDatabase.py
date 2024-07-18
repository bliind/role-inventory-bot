import aiosqlite

async def add_timed_role(role_id: int, expire_days: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            await db.execute('INSERT INTO timed_role (role_id, expire_days) VALUES (?, ?)', (role_id, expire_days))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add timed role:')
        print(e, role_id, expire_days)
        return False

async def update_timed_role(role_id: int, expire_days: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            await db.execute('UPDATE timed_role SET expire_days = ? WHERE role_id = ?', (expire_days, role_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to update timed role:')
        print(e, role_id, expire_days)
        return False

async def remove_timed_role(role_id: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            await db.execute('DELETE FROM timed_role WHERE role_id = ?', (role_id,))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to remove timed role:')
        print(e, role_id)
        return False

async def list_timed_roles():
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM timed_role')
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get timed roles:')
        print(e)
        return False

async def check_timed_role(role_id: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM timed_role WHERE role_id = ?', (role_id,))
            row = await cursor.fetchone()
            await cursor.close()
        if row:
            return row
    except Exception as e:
        print('Failed to check timed role:')
        print(e, role_id)
        return False

async def get_timed_roles():
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            cursor = await db.execute('SELECT role_id FROM timed_role')
            rows = await cursor.fetchall()
            await cursor.close()
        return [r[0] for r in rows]
    except Exception as e:
        print('Failed to get timed roles:')
        print(e)
        return False

async def add_timed_role_user(user_id: int, role_id: int, date_acquired: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            await db.execute('INSERT INTO timed_role_user (user_id, role_id, date_acquired) VALUES (?, ?, ?)', (user_id, role_id, date_acquired))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to add timed role user:')
        print(e, user_id, role_id, date_acquired)
        return False

async def get_users_roles(user_id: int):
    try:
        sql = '''
            SELECT * FROM timed_role_user
            JOIN timed_role ON timed_role.role_id = timed_role_user.role_id
            WHERE user_id = ?
        '''
        async with aiosqlite.connect('timed_roles.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (user_id,))
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get users roles expiration:')
        print(e)
        return False

async def get_expired_role_users(datestamp: int):
    try:
        sql = '''
            SELECT * FROM timed_role_user
            JOIN timed_role ON timed_role.role_id = timed_role_user.role_id
            WHERE ? - timed_role_user.date_acquired > (timed_role.expire_days * 86400)
        '''

        async with aiosqlite.connect('timed_roles.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (datestamp,))
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get expired role users:')
        print(e)
        return False
    
async def remove_role_user(user_id: int, role_id: int):
    try:
        async with aiosqlite.connect('timed_roles.db') as db:
            await db.execute('DELETE FROM timed_role_user WHERE user_id = ? AND role_id = ?', (user_id, role_id))
            await db.commit()
        return True
    except Exception as e:
        print('Failed to delete timed role user:')
        print(e, user_id, role_id)
        return False
