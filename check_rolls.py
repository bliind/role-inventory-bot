import aiosqlite
import datetime
import asyncio
import sys

dbfile = 'rockslots.db'

def humantime(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp)
    return date.strftime('%Y-%m-%d %H:%M:%S')

async def get_users_roles(user_id: int):
    try:
        sql = 'SELECT * FROM gamba WHERE user_id = ? ORDER BY datestamp ASC'

        async with aiosqlite.connect(dbfile) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, (user_id,))
            rows = await cursor.fetchall()
            await cursor.close()

        out = []
        for row in rows:
            out.append({
                "id": row['id'],
                "user_id": row['user_id'],
                "datestamp": row['datestamp'],
                "award": row['award']
            })
        return out
    except Exception as e:
        print(e)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemError('error: provide user id')

    rolls = asyncio.run(get_users_roles(sys.argv[1]))
    last = None
    for roll in rolls:
        if last:
            print(f'{humantime(roll["datestamp"])} (+{roll["datestamp"] - last} seconds)')
        else:
            print(humantime(roll['datestamp']))
        last = roll['datestamp']
