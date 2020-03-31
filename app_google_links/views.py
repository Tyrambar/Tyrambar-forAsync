import aiohttp_jinja2
from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid

import db
from forms import validate_login_form, check_passwords_form


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

# Main page for watch, download, delete links, add new link, delete own account and change password
@aiohttp_jinja2.template('index.html')
async def index(request):
    username = await authorized_userid(request)
    async with request.app['db_pool'].acquire() as conn:
        if not await conn.fetchrow(db.users2.select()):
            await db.create_sample_data(conn)

    if not username:
        raise redirect(request.app.router, 'login')
    changing_password = None
    async with request.app['db_pool'].acquire() as conn:
        current_user = await db.check_username(conn, username)
        links = await db.get_links4user(conn, current_user)

    if request.method == 'POST':
        form = await request.post()
        if form.get('change_password'):
            changing_password = 1
        else:
            async with request.app['db_pool'].acquire() as conn:
                if form.get('del_link'):
                    await db.delete_link(conn, request.match_info['id4del_link'])
                elif form.get('del_account'):
                    await db.delete_user(conn, username)
                elif form.get('past_password'):
                    if db.check_password(conn, username, form.get('past_password')):
                        if check_passwords_form(form.get('new_password'),
                                                form.get('check_new_password')):
                            db.change_password(conn, username, form.get('new_password'))
                else:
                    await db.create_link(conn, form.get('name_link'),
                                               form.get('url_link'), username)
            raise redirect(request.app.router, 'index')

    return {'user': current_user, 'links': links, 'changing_password': changing_password}

@aiohttp_jinja2.template('signup.html')
async def signup(request):
    username = await authorized_userid(request)
    if username:
        raise redirect(request.app.router, 'index')

    if request.method == 'POST':
        form = await request.post()

        async with request.app['db_pool'].acquire() as conn:
            wrong_login = await db.check_username(conn, form['future_name'])
            wrong_passw = check_passwords_form(form['future_password'],
                                               form['check_password'])
            if wrong_login:
                return {'error': 'Such login already exists'}
            elif wrong_passw:
                return {'error': 'Passwords don`t match'}
            else:
                await db.create_user(conn, form['future_name'], form['future_password'])
                response = redirect(request.app.router, 'login')
                raise response


@aiohttp_jinja2.template('login.html')
async def login(request):
    username = await authorized_userid(request)
    if username:
        raise redirect(request.app.router, 'index')

    if request.method == 'POST':
        form = await request.post()

        async with request.app['db_pool'].acquire() as conn:
            error = await validate_login_form(conn, form)
            if error:
                return {'error': error}
            else:
                response = redirect(request.app.router, 'index')

                user = await db.check_username(conn, form['login'])
                await remember(request, response, user['name'])

                raise response

async def logout(request):
    response = redirect(request.app.router, 'login')
    await forget(request, response)
    return response


