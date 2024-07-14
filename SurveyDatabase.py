import aiosqlite

async def create_survey(datestamp: int, channel_id: int, message_id: int, expires: int):
    query = '''
        INSERT INTO `survey`
        (datestamp, channel_id, message_id, expires)
        VALUES (?, ?, ?, ?)
    '''
    bind = (datestamp, channel_id, message_id, expires)

    try:
        async with aiosqlite.connect('survey.db') as db:
            await db.execute(query, bind)
            await db.commit()
        return True
    except Exception as e:
        print('Failed to create survey:')
        print(e, datestamp, channel_id, message_id, expires)
        return False

async def add_survey_response(datestamp: int, channel_id: int, message_id: int, user_id: int, response: str):
    query = '''
        INSERT INTO `survey_response`
        (datestamp, channel_id, message_id, user_id, response)
        VALUES (?, ?, ?, ?, ?)
    '''
    bind = (datestamp, channel_id, message_id, user_id, response)

    try:
        async with aiosqlite.connect('survey.db') as db:
            await db.execute(query, bind)
            await db.commit()
        return True
    except Exception as e:
        print('Failed to create survey response:')
        print(e, datestamp, channel_id, message_id, user_id, response)
        return False

async def list_surveys():
    try:
        async with aiosqlite.connect('survey.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM survey')
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to list surveys:')
        print(e)
        return False

async def get_results(channel_id: int, message_id: int):
    query = '''
        SELECT
            COUNT(response) AS count,
            response
        FROM survey_response
        WHERE channel_id = ?
        AND message_id = ?
        GROUP BY response
    '''
    bind = (channel_id, message_id)
    try:
        async with aiosqlite.connect('survey.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, bind)
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
    except Exception as e:
        print('Failed to get survey results:')
        print(e, channel_id, message_id)
        return False

async def get_latest_survey():
    query = 'SELECT * FROM survey ORDER BY datestamp DESC LIMIT 1'
    try:
        async with aiosqlite.connect('survey.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query)
            row = await cursor.fetchone()
            await cursor.close()
        if row:
            return row
    except Exception as e:
        print('Failed to get latest survey:')
        print(e)
        return False

async def check_user_answered(channel_id, message_id, user_id):
    query = '''
        SELECT response
        FROM survey_response
        WHERE channel_id = ?
        AND message_id = ?
        AND user_id = ?
    '''
    bind = (channel_id, message_id, user_id)
    try:
        async with aiosqlite.connect('survey.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, bind)
            row = await cursor.fetchone()
            await cursor.close()
        if row:
            return row
        else:
            return False
    except Exception as e:
        print('Failed to check if user answered:')
        print(e, channel_id, message_id, user_id)
        return False
