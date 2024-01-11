import aiosqlite
import uuid

async def save_slot_pull(user_id, datestamp):
    try:
        async with aiosqlite.connect('slots.db') as db:
            await db.execute('INSERT INTO gamba (id, user_id, datestamp) VALUES (?, ?, ?)', (str(uuid.uuid4()), user_id, datestamp))
            await db.commit()
    except Exception as e:
        print('Failed to save slot pull:')
        print(e, user_id, datestamp)

async def get_last_slot_pull(user_id):
    try:
        async with aiosqlite.connect('slots.db') as db:
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
