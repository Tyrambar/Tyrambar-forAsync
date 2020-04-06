import aiohttp_jinja2
from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid

import db
import forms


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)


@aiohttp_jinja2.template('index.html')
async def index(request):
    curr_user = await authorized_userid(request)
    async with request.app['db_pool'].acquire() as conn:
        if not await conn.fetchrow(db.users.select()):
            await db.create_sample_data(conn)
    if not curr_user:
        raise redirect(request.app.router, 'login')

    changing_password = None
    async with request.app['db_pool'].acquire() as conn:
        checked_curr_user = await db.check_login(conn, curr_user)
        links = await db.get_links4user(conn, checked_curr_user['login'])

    if request.method == 'POST':
        form = await request.post()
        if form.get('change_password'):
            changing_password = 1
        else:
            await forms.execute_main(request, form, curr_user)
            raise redirect(request.app.router, 'index')

    return {'user': curr_user, 'links': links,
            'changing_password': changing_password}


@aiohttp_jinja2.template('signup.html')
async def signup(request):
    curr_user = await authorized_userid(request)
    if curr_user:
        raise redirect(request.app.router, 'index')

    if request.method == 'POST':
        form = await request.post()
        checking_valid_signup = await forms.validate_signup(request, form)
        if checking_valid_signup:
            return checking_valid_signup
        raise redirect(request.app.router, 'login')


@aiohttp_jinja2.template('login.html')
async def login(request):
    curr_user = await authorized_userid(request)
    if curr_user:
        raise redirect(request.app.router, 'index')

    if request.method == 'POST':
        form = await request.post()

        async with request.app['db_pool'].acquire() as conn:
            error = await forms.validate_login(conn, form)
            if error:
                return {'error': error}
            else:
                response = redirect(request.app.router, 'index')

                checked_curr_user = await db.check_login(conn, form['login'])
                await remember(request, response, checked_curr_user['login'])

                raise response


async def logout(request):
    response = redirect(request.app.router, 'login')
    await forget(request, response)
    return response


