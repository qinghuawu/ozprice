from aiohttp import web
from views import setup_routes
import aiohttp_jinja2
import jinja2
from chemist_spyder import start_spyder, close_spyder
from orm import create_pool, close_pool
from models import check_user
from config_default import config
import aioredis


async def setup_redis(app, **kwargs):
    app['redis_pool'] = await aioredis.create_redis_pool(kwargs.get('host', 'redis://localhost'))


async def close_redis(app):
    app['redis_pool'].close()
    await app['redis_pool'].wait_closed()


async def init_app():
    app = web.Application()
    app['config'] = config
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    setup_routes(app)
    app.on_startup.append(create_pool)
    app.on_startup.append(check_user)
    app.on_startup.append(setup_redis)
    app.on_startup.append(start_spyder)
    app.on_cleanup.append(close_pool)
    app.on_cleanup.append(close_redis)
    app.on_cleanup.append(close_spyder)
    return app


def main():
    web.run_app(init_app(), host='127.0.0.1', port=9000)


if __name__ == '__main__':
    main()
