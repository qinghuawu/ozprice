from aiohttp import web
import aiohttp_jinja2
from config_default import config
from models import Chemist

routes = web.RouteTableDef()


def format_percent(d):
    d['discount'] = str(round(float(d['discount']) * 100)) + '%'
    if len(d['title_chinese']) > 27:
        d['title_chinese'] = d['title_chinese'][:24] + '...'
    return d


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)


@routes.get('/', name='index')
@aiohttp_jinja2.template('index.html')
async def index(request):
    redis_pool = request.app['redis_pool']
    keys = await redis_pool.keys('top*')
    if keys:
        print('Loading data from redis')
        cheapest_products = [await redis_pool.hgetall(key, encoding='utf-8') for key in keys]
        cheapest_products.sort(key=lambda x: x['title_chinese'])
    else:
        print('Loading data from mysql')
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


def setup_routes(app):
    app.add_routes(routes)
