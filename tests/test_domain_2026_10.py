"""Новый адрес MAX и сертификат Минцифры (октябрь 2026): `maxapi/client/domain.py`.

Запуск из корня форка: `python -m pytest tests/ -q` (нужны pytest,
pytest-asyncio и certifi). Сеть не нужна: «сертификат Минцифры» в тестах —
учебный корневой `tests/data/test_ca.pem`, им подписан сертификат локального
HTTPS-сервера `tests/data/test_server.pem` (127.0.0.1, срок — до 2126 года).
"""

import logging
import ssl

from pathlib import Path

import certifi
import pytest

from aiohttp import web

from maxapi import Bot
from maxapi.client.domain import (
    CA_BUNDLE_ENV, NEW_API_URL, OLD_API_URL, choose_api, ssl_context_with_bundle,
)
from maxapi.connection.base import BaseConnection
from maxapi.enums.http_method import HTTPMethod
from maxapi.enums.upload_type import UploadType
from maxapi.exceptions.max import MaxConnection


DATA = Path(__file__).parent / 'data'
TEST_CA = DATA / 'test_ca.pem'
TEST_CA_SUBJECT = ((('commonName', 'Test CA maxapi (tests only)'),),)


def _certifi_count() -> int:
    return ssl.create_default_context(cafile=certifi.where()).cert_store_stats()['x509_ca']


def _subjects(context: ssl.SSLContext) -> list:
    return [c['subject'] for c in context.get_ca_certs()]


@pytest.fixture
def bot_log(caplog):
    caplog.set_level(logging.INFO, logger='bot')
    return caplog


@pytest.fixture
def der_ca(tmp_path) -> Path:
    path = tmp_path / 'mincifry.cer'
    path.write_bytes(ssl.PEM_cert_to_DER_cert(TEST_CA.read_text()))
    return path


# --- 1. Выбор адреса --------------------------------------------------------

@pytest.mark.parametrize('value', [None, '', '   '])
def test_no_variable_keeps_the_old_address_silently(value, bot_log):
    assert choose_api(value) == (OLD_API_URL, None)
    assert bot_log.records == []


def test_bundle_file_switches_to_the_new_address(bot_log):
    url, context = choose_api(str(TEST_CA))

    assert url == NEW_API_URL == 'https://platform-api2.max.ru'
    assert isinstance(context, ssl.SSLContext)
    assert [r.levelname for r in bot_log.records] == ['INFO']


def test_missing_file_is_one_log_line_and_the_old_address(tmp_path, bot_log):
    missing = tmp_path / 'нет_такого.pem'

    assert choose_api(str(missing)) == (OLD_API_URL, None)
    assert OLD_API_URL == 'https://botapi.max.ru'
    assert len(bot_log.records) == 1
    record = bot_log.records[0]
    assert record.levelname == 'WARNING'
    assert str(missing) in record.getMessage()


def test_directory_instead_of_file_counts_as_missing(tmp_path, bot_log):
    assert choose_api(str(tmp_path)) == (OLD_API_URL, None)
    assert len(bot_log.records) == 1


def test_broken_file_is_one_log_line_and_the_old_address(tmp_path, bot_log):
    broken = tmp_path / 'mincifry.pem'
    broken.write_text('это не сертификат')

    assert choose_api(str(broken)) == (OLD_API_URL, None)
    assert len(bot_log.records) == 1
    assert bot_log.records[0].levelname == 'WARNING'


# --- 2. Контекст: certifi ПЛЮС файл -----------------------------------------

def test_context_is_certifi_plus_the_pem_file():
    context = ssl_context_with_bundle(str(TEST_CA))

    assert context.cert_store_stats()['x509_ca'] == _certifi_count() + 1
    assert TEST_CA_SUBJECT in _subjects(context)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_der_file_is_read_too(der_ca):
    context = ssl_context_with_bundle(str(der_ca))

    assert context.cert_store_stats()['x509_ca'] == _certifi_count() + 1
    assert TEST_CA_SUBJECT in _subjects(context)


# --- 3. Бот берёт адрес из переменной окружения -----------------------------

def test_bot_without_variable_is_as_before(monkeypatch):
    monkeypatch.delenv(CA_BUNDLE_ENV, raising=False)
    bot = Bot(token='тест')

    assert bot.API_URL == OLD_API_URL
    assert bot.ssl_context is None
    assert bot._ssl() is True


def test_bot_with_variable_goes_to_the_new_address(monkeypatch):
    monkeypatch.setenv(CA_BUNDLE_ENV, str(TEST_CA))
    bot = Bot(token='тест')

    assert bot.API_URL == NEW_API_URL
    assert bot._ssl() is bot.ssl_context
    assert TEST_CA_SUBJECT in _subjects(bot.ssl_context)


def test_bot_with_missing_file_stays_on_the_old_address(monkeypatch, tmp_path, bot_log):
    monkeypatch.setenv(CA_BUNDLE_ENV, str(tmp_path / 'нет.pem'))
    bot = Bot(token='тест')

    assert (bot.API_URL, bot.ssl_context) == (OLD_API_URL, None)
    assert len(bot_log.records) == 1


# --- 4. Живой SSL на локальном HTTPS-сервере --------------------------------

async def _start(app: web.Application, ssl_context=None):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0, ssl_context=ssl_context)
    await site.start()
    port = runner.addresses[0][1]
    scheme = 'https' if ssl_context else 'http'
    return runner, f'{scheme}://127.0.0.1:{port}'


def _app() -> web.Application:
    async def me(request: web.Request):
        return web.json_response({'ok': True})

    async def upload(request: web.Request):
        await request.read()
        return web.Response(text='{"token": "загружено"}')

    async def media(request: web.Request):
        return web.Response(body='картинка'.encode())

    app = web.Application()
    app.router.add_get('/me', me)
    app.router.add_post('/upload', upload)
    app.router.add_get('/media', media)
    return app


@pytest.fixture
async def https_server():
    """HTTPS с сертификатом, который подписан учебным «Минцифры»."""
    server_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_context.load_cert_chain(DATA / 'test_server.pem', DATA / 'test_server.key')
    runner, url = await _start(_app(), server_context)
    yield url
    await runner.cleanup()


@pytest.fixture
async def http_server():
    runner, url = await _start(_app())
    yield url
    await runner.cleanup()


def _bot_at(url: str, monkeypatch, bundle) -> Bot:
    if bundle is None:
        monkeypatch.delenv(CA_BUNDLE_ENV, raising=False)
    else:
        monkeypatch.setenv(CA_BUNDLE_ENV, str(bundle))
    bot = Bot(token='тест')
    bot.API_URL = url
    return bot


def _connection(bot: Bot) -> BaseConnection:
    """Как методы форка: отдельный объект запроса со ссылкой на бота."""
    connection = BaseConnection()
    connection.bot = bot
    return connection


@pytest.mark.asyncio
@pytest.mark.parametrize('bundle', [TEST_CA, 'der'])
async def test_api_request_passes_ssl_with_the_bundle(https_server, monkeypatch, bundle, der_ca):
    bot = _bot_at(https_server, monkeypatch, der_ca if bundle == 'der' else bundle)
    try:
        raw = await bot.request(HTTPMethod.GET, '/me', is_return_raw=True)
    finally:
        await bot.close_session()

    assert raw == {'ok': True}


@pytest.mark.asyncio
async def test_api_request_fails_ssl_without_the_bundle(https_server, monkeypatch):
    bot = _bot_at(https_server, monkeypatch, None)
    try:
        with pytest.raises(MaxConnection, match='certificate'):
            await bot.request(HTTPMethod.GET, '/me', is_return_raw=True)
    finally:
        await bot.close_session()


@pytest.mark.asyncio
async def test_upload_and_download_use_the_same_context(https_server, monkeypatch, tmp_path):
    """Загрузка вложений идёт отдельной сессией на адрес от MAX — SSL тот же."""
    bot = _bot_at(https_server, monkeypatch, TEST_CA)
    connection = _connection(bot)

    text = await connection.upload_file_buffer(
        filename='картинка', url=f'{https_server}/upload', buffer=b'\x89PNG', type=UploadType.IMAGE,
    )
    assert text == '{"token": "загружено"}'

    picture = tmp_path / 'p.png'
    image = tmp_path / 'i.png'
    image.write_bytes(b'\x89PNG')
    assert await connection.upload_file(
        url=f'{https_server}/upload', path=str(image), type=UploadType.IMAGE,
    ) == '{"token": "загружено"}'
    assert await connection.download_file(
        path=str(picture), url=f'{https_server}/media', token='т',
    ) == 200
    assert picture.read_bytes() == 'картинка'.encode()


@pytest.mark.asyncio
async def test_upload_without_the_bundle_fails_ssl(https_server, monkeypatch):
    bot = _bot_at(https_server, monkeypatch, None)

    with pytest.raises(Exception, match='certificate'):
        await _connection(bot).upload_file_buffer(
            filename='картинка', url=f'{https_server}/upload', buffer=b'\x89PNG',
            type=UploadType.IMAGE,
        )


@pytest.mark.asyncio
async def test_plain_http_still_works_with_the_bundle(http_server, monkeypatch):
    """Подмены MAX в тестах бота ходят по http — контекст им не мешает."""
    bot = _bot_at(http_server, monkeypatch, TEST_CA)
    try:
        raw = await bot.request(HTTPMethod.GET, '/me', is_return_raw=True)
    finally:
        await bot.close_session()

    assert raw == {'ok': True}
