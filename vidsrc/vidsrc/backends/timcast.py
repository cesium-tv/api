import re
import json
import asyncio
import logging
from urllib.parse import urljoin

import pyppeteer
from pyppeteer.errors import PyppeteerError
from aiohttp_scraper import ScraperSession
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

RUMBLE_DOMAIN = re.compile(r'^https://rumble.com/embed/')
JSON_EXTRACT = re.compile(r'g\.f\["\w{6,7}"\]=({.*}),loaded:d\(\)')
JSON_TRIM = re.compile(r'^(.*)"path":.*,("w":.*$)')


class LimitReached(Exception):
    def __init__(self):
        super().__init__('Limit reached')


class DepthReached(Exception):
    def __init__(self):
        super().__init__('Depth reached')


def _no_images(request):
    if request.resourceType() == 'image':
        request.abort_()
    else:
        request.continue_()


async def _login(options, headless=True, timeout=2000):
    url = options['url']
    u_field, u_value = options['username']
    p_field, p_value = options['password']
    submit = options['submit']

    browser = await pyppeteer.launch(
        headless=headless,
        args=[
            '--start-maximized',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ],
        ignoreHTTPSError=True,
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )

    page = await browser.newPage()

    try:
        await page.setViewport({ 'width': 1366, 'height': 768 })

        LOGGER.debug('opening url: %s', url)
        await page.goto(url, timeout=timeout, waitFor='networkidle2')

        LOGGER.debug('typing')
        await page.type(u_field, u_value)
        await page.type(p_field, p_value)

        LOGGER.debug('clicking submit')
        await page.click(submit)

        cookieStr = []
        for cookie in await page.cookies():
            cookieStr.append(f"{cookie['name']}={cookie['value']}")
        return '; '.join(cookieStr)

    finally:
        await page.close()
        await browser.close()


async def login(options, headless=True, retry=3):
    for i in range(1, 1 + retry):
        try:
            LOGGER.debug('Login attempt %i', i + 1)
            return await _login(options['login'], headless=headless, timeout=2000 * i)

        except (PyppeteerError, asyncio.TimeoutError):
            if i == retry:
                raise

            LOGGER.exception('Login failed, retrying')
            await asyncio.sleep(3 ** i)


async def _download(name, url, options):
    cookies = await login(options)
    whitelist = options.get('whitelist', [])
    limit = options.get('limit')
    
    seen = set()
    videos = []

    async def _handle(url, depth):
        LOGGER.debug('url: %s', url)
        if depth is not None:
            if depth == 0:
                raise DepthReached()
            depth -= 1

        if url in seen:
            LOGGER.debug('Skipping duplicate url')
            return
        seen.add(url)

        async with ScraperSession() as session:
            r = await session.get_html(url, headers={'cookie': cookies})
            LOGGER.debug('Got %i bytes', len(r))

        soup = BeautifulSoup(r, 'html.parser')

        srcSeen = set()
        for iframe in soup.find_all('iframe'):
            LOGGER.debug('Found iframe')
            src = iframe['src']
            LOGGER.info('src: %s', src)
            if src in srcSeen:
                LOGGER.debug('Skipping duplicate iframe')
                continue
            if not src or not RUMBLE_DOMAIN.match(src):
                LOGGER.debug('Missing or invalid iframe src')
                continue
            srcSeen.add(src)

            async with ScraperSession() as session:
                r = await session.get_html(src, headers={'referer': url})
                LOGGER.debug('Received %i bytes', len(r))

            m = JSON_EXTRACT.search(r)
            if not m:
                LOGGER.warn(r)
                continue

            data = JSON_TRIM.sub(r'\1\2}', m.group(1))
            try:
                videos.append(data)
                yield json.loads(data)

            except (TypeError, ValueError) as e:
                LOGGER.exception('Invalid json')
                LOGGER.warn(data)

        for a in soup.find_all('a'):
            LOGGER.debug('Found anchor tag')
            href = a['href']
            if not href:
                LOGGER.debug('Missing or invalid href')
                continue

            href = urljoin(url, href)
            LOGGER.debug('href: %s', href)
            if href in seen:
                LOGGER.debug('Skipping duplicate href')
                continue

            if not any([re.match(p, href) for p in whitelist]):
                LOGGER.debug('Skipping invalid href')
                continue

            if limit is not None:
                LOGGER.debug('Video count: %i of %i', len(videos), limit)
                if len(videos) >= limit:
                    raise LimitReached()

            async for v in _handle(href, depth):
                yield v

    try:
        async for v in _handle(url, options.get('depth')):
            yield v

    except (LimitReached, DepthReached) as e:
        LOGGER.info(e.args[0])


def download(name, url, options):
    # NOTE: This code converts from async generator to sync generator.
    loop = asyncio.get_event_loop()
    ait = _download(name, url, options).__aiter__()

    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None

    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj
