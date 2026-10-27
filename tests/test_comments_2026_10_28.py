"""Комментарии к постам: чтение и события в той форме, в какой их шлёт живой MAX.

Образцы — из пробы ТП24 (28.10.2026, тестовый канал владельца бота
«Империя розыгрышей»): в событии `comment_created` у адресата
`chat_type: "chat"` и `post_id`, вложений в теле нет; комментарий владельца
канала приходит без `sender`; `comment_removed` — плоский. Сеть не нужна —
запросы уходят на локальный сервер-подмену.
"""

import pytest
from aiohttp import web

from maxapi import Bot
from maxapi.methods.types.getted_updates import process_update_request, process_update_webhook
from maxapi.types import CommentCreated, CommentRemoved, Comments

POST = 'mid.ffffb79d88bc7a7f01a17e65b9f83cf7'
SENDER = {'user_id': 310364131, 'first_name': 'Гость', 'is_bot': False, 'last_name': '',
          'last_activity_time': 1793125118000, 'name': 'Гость'}
CREATED = {
    'message': {
        'recipient': {'chat_type': 'chat', 'chat_id': -79587744908673, 'post_id': POST},
        'timestamp': 1793125131153,
        'body': {'mid': 'mid.ffffb79d88bc7a7f01a17e962391077f', 'seq': 117514248595244927, 'text': '+'},
        'sender': SENDER,
    },
    'timestamp': 1793125131153,
    'update_type': 'comment_created',
}
REMOVED = {
    'message_id': 'mid.ffffb79d88bc7a7f01a17e962391077f', 'chat_id': -79587744908673,
    'user_id': 310364131, 'post_id': POST, 'timestamp': 1793125131153, 'update_type': 'comment_removed',
}
PAGE = {'messages': [
    {'recipient': {'chat_type': 'channel', 'chat_id': -79587744908673, 'post_id': POST},
     'timestamp': 1793121967665,
     'body': {'mid': 'mid.ffffb79d88bc7a7f01a17e65de3140eb', 'seq': 117514041272910059, 'text': 'от канала'}},
    {'recipient': {'chat_type': 'channel', 'chat_id': -79587744908673, 'post_id': POST},
     'timestamp': 1793125131153, 'sender': SENDER,
     'link': {'type': 'reply', 'mid': 'mid.неизвестной-формы'},
     'body': {'mid': 'mid.ffffb79d88bc7a7f01a17e962391077f', 'seq': 117514248595244927, 'text': '+',
              'markup': [{'type': 'стиль-которого-ещё-нет', 'from': 0, 'length': 1}]}},
]}


@pytest.fixture
async def max_server():
    seen = []

    async def handler(request: web.Request):
        query = {k: v for k, v in request.query.items() if k != 'access_token'}
        seen.append({'method': request.method, 'path': request.path, 'query': query})
        return web.json_response(PAGE)

    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    yield f'http://127.0.0.1:{runner.addresses[0][1]}', seen
    await runner.cleanup()


def _bot(url: str) -> Bot:
    bot = Bot(token='тест')
    bot.API_URL = url
    return bot


@pytest.mark.asyncio
async def test_live_comment_created_parses_without_extra_request(max_server):
    url, seen = max_server
    bot = _bot(url)
    try:
        event = await process_update_webhook(dict(CREATED), bot)
    finally:
        await bot.close_session()
    assert isinstance(event, CommentCreated)
    assert event.message.recipient.post_id == POST
    assert event.message.sender.user_id == 310364131
    assert event.get_ids() == (-79587744908673, 310364131)
    # на каждый комментарий канала — ни одного запроса к MAX
    assert seen == []


@pytest.mark.asyncio
async def test_channel_comment_without_sender_and_flat_removal():
    owner = {**CREATED, 'message': {**CREATED['message']}}
    owner['message'].pop('sender')
    got = await process_update_request({'updates': [owner, REMOVED]}, Bot(token='тест'))
    assert [type(e) for e in got] == [CommentCreated, CommentRemoved]
    assert got[0].message.sender is None and got[0].get_ids() == (-79587744908673, None)
    assert (got[1].post_id, got[1].message_id, got[1].get_ids()) == (
        POST, 'mid.ffffb79d88bc7a7f01a17e962391077f', (-79587744908673, 310364131))


@pytest.mark.asyncio
async def test_get_comments_window(max_server):
    url, seen = max_server
    bot = _bot(url)
    try:
        page = await bot.get_comments(POST, after=10, before=20)
    finally:
        await bot.close_session()
    assert seen == [{'method': 'GET', 'path': f'/messages/{POST}/comments',
                     'query': {'count': '100', 'after': '10', 'before': '20'}}]
    assert isinstance(page, Comments)
    # незнакомые стиль разметки и форма ответа на комментарий страницу не роняют
    assert [(c.sender.user_id if c.sender else None, c.body.mid[-6:]) for c in page.messages] == [
        (None, '3140eb'), (310364131, '91077f')]


@pytest.mark.asyncio
async def test_get_comments_by_ids_ignores_window(max_server):
    url, seen = max_server
    bot = _bot(url)
    try:
        await bot.get_comments(POST, after=10, comment_ids=['a', 'b'])
    finally:
        await bot.close_session()
    assert seen[0]['query'] == {'comment_ids': 'a,b'}
