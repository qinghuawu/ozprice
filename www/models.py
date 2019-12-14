import time
import uuid
import aiomysql
from aiohttp import web
from security import generate_password_hash
import asyncio

from orm import Model, StringField, BooleanField, FloatField, TextField, IntegerField, create_pool
import orm


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=None, ddl='int(10)')
    password_hash = StringField(ddl='char(128)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Chemist(Model):
    __table__ = 'chemist'
    title = StringField(ddl='varchar(255)')
    title_chinese = StringField(ddl='varchar(255)')
    price = FloatField()
    original_price = FloatField()
    lowest_price = FloatField()
    discount = FloatField()
    category = StringField(ddl='varchar(100)')
    url = StringField(ddl='varchar(255)', primary_key = True)
    image = TextField()


async def get_users_by_name(conn, username, limit=1):
    return await User.findAll(conn, where=f'name = "{username}"', limit=limit)


async def generate_user(conn, **kw):
    # u = User(name='root', password_hash=generate_password_hash('password'), admin=1)
    u = User(name='kedaduck', password_hash=generate_password_hash('wqh930129'), admin=1)
    await u.save(conn)


async def check_user(app):
    async with app['db_pool'].acquire() as conn:
        if not await get_users_by_name(conn, 'kedaduck'):
            await generate_user(conn)


async def test():
    conn = await aiomysql.connect(host='127.0.0.1', port=3306, user='kedaduck', password='wqh930129', db='awesome',
                                  autocommit=True)
    await generate_user(conn)
    conn.close()
    # u = User(name='Test', email='test@qq.com', passwd='1234567890', image='about:blank')
    # c = Chemist(title='HAHAHA', title_chinese='我是谁', price=156.6, original_price=138.2, discount=0.78, category='男人', url='http://', image='www.a')
    # await u.save()
    # await c.save()
    # a = await User.findAll(app, where='name = "wqh"', limit=1)
    # print(a)
    # await orm.close_pool(app)


if __name__ == '__main__':
    asyncio.run(test())
    # web.run_app(app, host='127.0.0.1', port=9000)
