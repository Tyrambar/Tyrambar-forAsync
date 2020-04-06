import ssl
import os

import asyncpgsa
from sqlalchemy import (
    create_engine,
    MetaData, Table, Column, ForeignKey,
    Integer, String
)
from sqlalchemy.sql import select


BEGIN_URL_GOOGLE = 'https://drive.google.com/open?id='

meta = MetaData()

users = Table(
    'users', meta,

    Column('id', Integer, primary_key=True),
    Column('login', String(30), unique=True, nullable=False),
    Column('password', String(32), nullable=False)
)

links = Table(
    'links', meta,

    Column('id', Integer, primary_key=True),
    Column('url', String(300), nullable=False),
    Column('name_url', String(150), nullable=False),
    Column('user_id',
           Integer,
           ForeignKey('users.id', ondelete='CASCADE'))
)


async def init_db(app):
    dsn = construct_db_url(app['config']['database'])
    ctx = ssl.create_default_context(
          cafile=os.path.join(os.path.dirname(__file__),
                              'config/path_to_your_ssl_sert'))
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    pool = await asyncpgsa.create_pool(dsn=dsn, ssl=ctx)
    app['db_pool'] = pool
    return pool


def construct_db_url(config):
    DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"
    return DSN.format(
        user=config['DB_USER'],
        password=config['DB_PASS'],
        database=config['DB_NAME'],
        host=config['DB_HOST'],
        port=config['DB_PORT']
    )


async def check_login(conn, login):
    result = await conn.fetchrow(
        users
        .select()
        .where(users.c.login == login)
    )
    return result


async def check_password(conn, login, password):
    result = await conn.fetchrow(
        users
        .select()
        .where(users.c.login == login)
        .where(users.c.password == password))
    return result


async def change_password(conn, login, password):
    await conn.execute("""UPDATE users 
                       SET users.password = $2 
                       WHERE users.login = $1""", login, password)


async def create_user(conn, login, password):
    await conn.execute(users.insert()
                       .values(login=login,
                               password=password))


async def delete_user(conn, login):
    await conn.execute(users.delete()
                       .where(users.c.login == login))


async def get_links4user(conn, login):
    j = links.join(users, links.c.user_id == users.c.id)
    exists_links = await conn.fetch(
        select([links]).
        select_from(j)
        .where(users.c.login == login))
    return exists_links


async def create_link(conn, name_url, url, link_user):
    if BEGIN_URL_GOOGLE in url:
        url = url.split('=')[1]
    user_id = await check_login(conn, link_user)
    stmt = links.insert().values(url=url,
                                 name_url=name_url,
                                 user_id=user_id['id'])
    await conn.execute(stmt)


async def delete_link(conn, link_id):
    stmt = links.delete().where(links.c.id == int(link_id))
    await conn.execute(stmt)


async def create_sample_data(conn):
    await conn.execute(users.insert()
                             .values(login='admin',
                                     password='admin'))

    stmt = links.insert().values(url='1FIBJzVQX42yrNshZVjMhVAR56PDbE2wb',
                                 name_url='new_link',
                                 user_id=1)
    await conn.execute(stmt)