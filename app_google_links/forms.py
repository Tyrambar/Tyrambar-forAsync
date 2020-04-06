import db


async def validate_signup(request, form):
    async with request.app['db_pool'].acquire() as conn:
        wrong_login = await db.check_login(conn, form['future_name'])
        wrong_passw = check_passwords(form['future_password'],
                                      form['check_password'])
        print('in valid', wrong_passw)
        if wrong_login:
            return {'error': 'Such login already exists'}
        elif wrong_passw:
            return {'error': 'Passwords don`t match'}
        else:
            await db.create_user(conn, form['future_name'],
                                 form['future_password'])
            return {}


async def validate_login(conn, form):
    checking_login = form['login']
    checking_password = form['password']
    if not checking_login:
        return 'name is required'
    if not checking_password:
        return 'password is required'

    user_data = await db.check_login(conn, checking_login)

    if not user_data['login']:
        return 'Invalid username'
    if not user_data['password']:
        return 'Invalid password'
    return None


async def execute_main(request, form, curr_user):
    async with request.app['db_pool'].acquire() as conn:
        if form.get('del_link'):
            await db.delete_link(conn, request.match_info['id4del_link'])
        elif form.get('del_account'):
            await db.delete_user(conn, curr_user)
        elif form.get('past_password'):
            if await db.check_password(conn, curr_user,
                                       form.get('past_password')):
                if check_passwords(form.get('new_password'),
                                   form.get('check_new_password')):
                    await db.change_password(conn, curr_user,
                                             form.get('new_password'))
        else:
            await db.create_link(conn, form.get('name_link'),
                                 form.get('url_link'), curr_user)


def check_passwords(passw1, passw2):
    print('paaaa', passw1, passw2)
    if passw1 != passw2:
        return True
    if len(passw1) < 5:
        return True
    return False

