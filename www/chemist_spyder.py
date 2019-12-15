import aiohttp
import asyncio
import re
import time
from bs4 import BeautifulSoup
import aiomysql
from models import Chemist


async def open_url(url, session, headers):
    async with session.get(url, headers=headers) as resp:
        data = await resp.text()
        soup = BeautifulSoup(data, 'lxml')
        return soup


async def get_product(soups, db_pool):
    data_to_save = []
    category = soups[0].find('span', attrs={'id': 'category_title_span'}).text.strip()
    for soup in soups:
        L = soup.find('div', attrs={'class': 'product-list-container'}).find_all('td')
        while not L[-1].text:
            L = L[:-1]
        for item in L:
            mapping = {'title_chinese': item.find('a').get('title').strip(),
                       'title': item.find('img').get('alt').strip(),
                       'price': float(item.find('span').text.strip()[1:]),
                       'url': 'https://www.chemistwarehouse.com.au' + item.find('a').get('href'),
                       'image': item.find('img').get('src'),
                       'category': category}

            mapping['original_price'] = mapping['price'] + (
                float(item.find('span', attrs={'class': 'Save'}).text.strip()[4:]) if item.find('span',
                                                                                                attrs={
                                                                                                    'class': 'Save'}) else 0)
            mapping['lowest_price'] = mapping['price']
            mapping['discount'] = (mapping['original_price'] - mapping['price']) / mapping['original_price']
            data_to_save.append(mapping)

    stmt_insert = "INSERT INTO chemist " \
                  "(title, title_chinese, price, original_price, lowest_price, discount, category, url, image)" \
                  "VALUES(%(title)s, %(title_chinese)s, %(price)s, %(original_price)s, %(lowest_price)s," \
                  "%(discount)s, %(category)s, %(url)s, %(image)s) ON DUPLICATE KEY UPDATE " \
                  "title=%(title)s, title_chinese=%(title_chinese)s, price=%(price)s," \
                  "original_price=%(original_price)s, discount=%(discount)s, category=%(category)s, image=%(image)s," \
                  "lowest_price=if(lowest_price<%(lowest_price)s, lowest_price, %(lowest_price)s);"

    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.executemany(stmt_insert, data_to_save)


async def item_by_category(category, session, headers, db_pool):
    url = 'https://www.chemistwarehouse.hk/Shop-OnLine/' + category + '?size=120'
    print(category, 'started at', time.strftime('%X'))
    soup = await open_url(url, session, headers)
    soups = [soup]
    if soup.find('a', attrs={'class': 'last-page'}):
        last = int(re.search(r'\d+$', soup.find('a', attrs={'class': 'last-page'}).get('href')).group())
        for page in range(2, last + 1):
            await asyncio.sleep(0.1)
            soups.append(await open_url(url + '&page=' + str(page), session, headers))
    await get_product(soups, db_pool)
    print(category, 'done!', time.strftime('%X'))


async def init_spyder(app):
    try:
        while True:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Connection': 'keep-alive'
                }
                categories = ['256/health', '257/beauty', '258/medicines', '259/personal-care', '260/medical-aids']
                await asyncio.gather(*[item_by_category(x, session, headers, app['db_pool']) for x in categories])

                async with app['db_pool'].acquire() as conn:
                    cheapest_products = await Chemist.findAll(conn, where='price=lowest_price and discount != 0',
                                                              orderBy='title_chinese', limit=220)
                    timeout = 3.5*60*60
                    for i, product in enumerate(cheapest_products):
                        await app['redis_pool'].hmset_dict(f'top_{i}', product)
                        await app['redis_pool'].expire(f'top_{i}', timeout)
            await asyncio.sleep(3*60*60)
    except asyncio.CancelledError:
        pass
    finally:
        if session:
            await session.close()


async def start_spyder(app):
    app['chemist_spyder'] = asyncio.create_task(init_spyder(app))


async def close_spyder(app):
    app['chemist_spyder'].cancel()
    await app['chemist_spyder']


async def main_test():
    db_pool = await aiomysql.create_pool(user='root', password='password', db='awesome', host='127.0.0.1',
                                         autocommit=True)
    async with aiohttp.ClientSession() as session:
        headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive'
        }
        categories = ['256/health', '257/beauty', '258/medicines', '259/personal-care', '260/medical-aids']
        await asyncio.gather(*[item_by_category(x, session, headers, db_pool) for x in categories])

    db_pool.close()
    await db_pool.wait_closed()


if __name__ == '__main__':
    asyncio.run(main_test())
