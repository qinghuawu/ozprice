from security import check_password_hash
from models import get_users_by_name


async def validate_login_form(app, form):

    username = form['username']
    password = form['password']

    if not username:
        return 'username is required'
    if not password:
        return 'password is required'

    user = await get_users_by_name(app, username)

    if not user:
        return 'Invalid username'
    user = user[0]
    if not check_password_hash(password, user['password_hash']):
        return 'Invalid password'
    else:
        return None
