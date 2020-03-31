import db


async def validate_login_form(conn, form):
    username = form['login']
    password = form['password']
    if not username:
        return 'name is required'
    if not password:
        return 'password is required'

    user = await db.check_username(conn, username)

    if not user:
        return 'Invalid username'
    if not user['password']:
        return 'Invalid password'
    else:
        return None

async def check_passwords_form(passw1, passw2):
    if passw1 != passw2:
        return False
    if len(passw1) < 6:
        return False
    return True

