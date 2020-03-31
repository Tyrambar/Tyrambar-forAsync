import asyncpgsa
from sqlalchemy import (
    create_engine,
    MetaData, Table, Column, ForeignKey,
    Integer, String
)
from sqlalchemy.sql import select

import ssl
import os

BEGIN_URL_GOOGLE = 'https://drive.google.com/open?id='


meta = MetaData()

users2 = Table(
    'users2', meta,

    Column('id', Integer, primary_key=True),
    Column('name', String(30), unique=True, nullable=False),
    Column('password', String(32), nullable=False)
)

links = Table(
    'links', meta,

    Column('id', Integer, primary_key=True),
    Column('url', String(300), nullable=False),
    Column('name_url', String(150), nullable=False),
    Column('user2_id',
           Integer,
           ForeignKey('users2.id', ondelete='CASCADE'))
)

async def init_db(app):
    dsn = construct_db_url(app['config']['database'])
	# This code helps connect to DB like heroku, where need SSL
    ctx = ssl.create_default_context(cafile=os.path.join(os.path.dirname(__file__), 'rds-combined-ca-bundle.pem'))
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

# Check input form username
async def check_username(conn, username):
    result = await conn.fetchrow(
        users2
        .select()
        .where(users2.c.name == username)
    )
    return result

# Check input form password
async def check_password(conn, username, passw):
    result = await conn.fetchrow(
        users2
        .select()
        .where(users2.c.name == username,
               users2.c.password == passw))
    return result

async def change_password(conn, username, passw):
    await conn.execute("""UPDATE users2 
                       SET users2.password = $2 
                       WHERE users2.name = $1""", username, passw)

async def create_user(conn, usern, passw):
    await conn.execute(users2.insert()
                       .values(name=usern,
                               password=passw))

async def delete_user(conn, usern):
    await conn.execute(users2.delete()
                       .where(users2.c.name == usern))

# Return records of links from DB by username
async def get_links4user(conn, username):
    j = links.join(users2, links.c.user2_id == users2.c.id)
    exists_links = await conn.fetch(
        select([links]).
        select_from(j)
            .where(users2.c.name == username['name']))
    return exists_links

async def create_link(conn, name_link, url_link, link_user):
    if BEGIN_URL_GOOGLE in url_link:
        url_link = url_link.split('=')[1]
    user_id = await check_username(conn, link_user)
    stmt = links.insert().values(url=url_link,
                                 name_url=name_link,
                                 user2_id= user_id['id'])
    await conn.execute(stmt)

async def delete_link(conn, link_id):
    stmt = links.delete().where(links.c.id == int(link_id))
    await conn.execute(stmt)

async def create_sample_data(conn):
    await conn.execute(users2.insert()
                             .values(name='admin',
                                     password='admin'))

    stmt = links.insert().values(url='1FIBJzVQX42yrNshZVjMhVAR56PDbE2wb',
                                 name_url='new_link',
                                 user2_id=1)
    await conn.execute(stmt)

