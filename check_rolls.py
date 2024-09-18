import aiosqlite
import datetime
import asyncio
import sys

dbfile = 'rockslots.db'

def humantime(timestamp):
    date = datetime.datetime.fromtimestamp(timestamp)
    return date.strftime('%Y-%m-%d %H:%M:%S')

async def get_user_spins(user_id: int):
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

async def get_spin_counts():
    try:
        sql = 'SELECT count(id) as total_spins, user_id FROM gamba GROUP BY user_id ORDER BY total_spins ASC'

        async with aiosqlite.connect(dbfile) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql)
            rows = await cursor.fetchall()
            await cursor.close()

        out = []
        for row in rows:
            out.append({
                "total_spins": row['total_spins'],
                "user_id": row['user_id'],
            })
        return out
    except Exception as e:
        print(e)
        return False

async def get_rewards_counts():
    try:
        sql = 'SELECT COUNT(award) AS count, award FROM gamba GROUP BY award ORDER BY count DESC'

        async with aiosqlite.connect(dbfile) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql)
            rows = await cursor.fetchall()
            await cursor.close()

        out = []
        for row in rows:
            out.append({
                "award": row['award'],
                "count": row['count'],
            })
        return out
    except Exception as e:
        print(e)
        return False

def check_user_spins(user_id: int):
    rolls = asyncio.run(get_user_spins(user_id))
    last = None
    for roll in rolls:
        if last:
            print(f'{humantime(roll["datestamp"])} (+{roll["datestamp"] - last} seconds)')
        else:
            print(humantime(roll['datestamp']))
        last = roll['datestamp']
    print(f'Total: {len(rolls)}')

def check_total_spins():
    rolls = asyncio.run(get_spin_counts())
    for roll in rolls:
        print(f'{roll["user_id"]} - {roll["total_spins"]}')

def check_reward_totals():
    awards = asyncio.run(get_rewards_counts())
    for award in awards:
        print(f'{award["award"]} - {award["count"]}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemError('error: provide action')

    if sys.argv[1] == 'user':
        if len(sys.argv) < 3:
            raise SystemError('error: provide user id')
        check_user_spins(sys.argv[2])

    elif sys.argv[1] == 'totals':
        check_total_spins()

    elif sys.argv[1] == 'rewards':
        check_reward_totals()
