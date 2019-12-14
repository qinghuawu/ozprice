from aiohttp import web
import aiohttp_jinja2
from config_default import config
from models import Chemist
from forms import validate_login_form
from models import get_users_by_name

routes = web.RouteTableDef()


def format_percent(d):
    d['discount'] = str(round(d['discount'] * 100)) + '%'
    if len(d['title_chinese']) > 27:
        d['title_chinese'] = d['title_chinese'][:24] + '...'
    return d


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)


@routes.get('/', name='index')
@aiohttp_jinja2.template('index.html')
async def index(request):
    # username = await authorized_userid(request)
    # if not username:
    #     raise redirect(request.app.router, 'login')
    async with request.app['db_pool'].acquire() as conn:
        cheapest_products = await Chemist.findAll(conn, where='price=lowest_price and discount != 0',
                                                  orderBy='title_chinese', limit=220)
        cheapest_products = [format_percent(product) for product in cheapest_products]
        cheapest_products = [cheapest_products[x: x+5] for x in range(0, len(cheapest_products), 5)]
    return {'user': config['db']['user'],
            'cheapest_products': cheapest_products}


@routes.get('/discount', name='discount')
@aiohttp_jinja2.template('discount.html')
async def index(request):
    async with request.app['db_pool'].acquire() as conn:
        discount_products = await Chemist.findAll(conn, orderBy='discount DESC, title_chinese', limit=220)
        discount_products = [format_percent(product) for product in discount_products]
        discount_products = [discount_products[x: x+5] for x in range(0, len(discount_products), 5)]
    return {'user': config['db']['user'],
            'discount_products': discount_products}


# @routes.get('/login', name='login')
# @aiohttp_jinja2.template('login.html')
# async def login(request):
#     return {}
#
#
# @routes.post('/login', name='login')
# @aiohttp_jinja2.template('login.html')
# async def login(request):
#     username = await authorized_userid(request)
#     if username:
#         raise redirect(request.app.router, 'index')
#
#     form = await request.post()
#
#     async with request.app['db_pool'].acquire() as conn:
#         error = await validate_login_form(conn, form)
#
#         if error:
#             return {'error': error}
#         else:
#             response = redirect(request.app.router, 'index')
#
#             users = await get_users_by_name(conn, form['username'])
#             user = users[0]
#             await remember(request, response, user['name'])
#             raise response
#
#     return {}


def setup_routes(app):
    app.add_routes(routes)
