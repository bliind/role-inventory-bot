import aiosqlite
import uuid

async def save_slot_pull(user_id, datestamp, award):
    try:
        async with aiosqlite.connect('rockslots.db') as db:
            await db.execute('INSERT INTO gamba (id, user_id, datestamp, award) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), user_id, datestamp, str(award)))
            await db.commit()
    except Exception as e:
        print('Failed to save slot pull:')
        print(e, user_id, datestamp)

async def get_last_slot_pull(user_id):
    try:
        async with aiosqlite.connect('rockslots.db') as db:
            cursor = await db.execute('SELECT * FROM gamba WHERE user_id = ? ORDER BY datestamp DESC', (user_id,))
            row = await cursor.fetchone()
    except Exception as e:
        print('Failed to get slot pull:')
        print(e, user_id)

    try:
        return {
            "id":        row[0],
            "user_id":   row[1],
            "datestamp": row[2]
        }
    except:
        return None

async def get_total_pulls(user_id):
    try:
        async with aiosqlite.connect('rockslots.db') as db:
            cursor = await db.execute('SELECT count(id) AS count FROM gamba WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
    except Exception as e:
        print('Failed to get total pulls:')
        print(e, user_id)

    return row[0]

async def get_stats(user_id):
    out = []
    try:
        async with aiosqlite.connect('rockslots.db') as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT count(id) as count, award FROM gamba WHERE user_id = ? GROUP BY award', (user_id,)) as cursor:
                async for row in cursor:
                    out.append(row)
        return out
    except Exception as e:
        print('Failed to get stats:')
        print(e, user_id)
        return False


async def get_hot_hour():
    try:
        async with aiosqlite.connect('rockslots.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM hot_hour')
            row = await cursor.fetchone()
    except Exception as e:
        print('Failed to get hot hour data:')
        print(e)
        return

    return row

async def change_hot_hour(hour=None, active=None, odds=None):
    changes = {}
    params = {"hour": hour, "active": active, "odds": odds}
    for f,v in params.items():
        if v != None: changes[f] = v

    sql = 'UPDATE hot_hour SET ('
    sql += ','.join(changes.keys()) + ') = ('
    sql += ','.join(['?' for i in changes.keys()]) + ')'

    try:
        async with aiosqlite.connect('rockslots.db') as db:
            await db.execute(sql, list(changes.values()))
            await db.commit()
    except Exception as e:
        print('Failed to change hot hour:')
        print(e, hour, active, odds)

