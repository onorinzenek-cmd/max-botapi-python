"""Пользователь без `last_activity_time`: разбор не падает.

Документация MAX (объект User): поле может не прийти, если человек скрыл
«в сети». У удалённого аккаунта его нет вовсе — 29.10.2026 список админов
канала с 'DELETED USER' ронял `get_list_admin_chat` (ValidationError
members.3.last_activity_time). Сеть не нужна — запросы уходят на локальный
сервер-подмену.
"""

import pytest
from aiohttp import web

from maxapi import Bot
from maxapi.methods.types.getted_updates import process_update_request
from maxapi.methods.types.getted_list_admin_chat import GettedListAdminChat
from maxapi.types import MessageCreated
from maxapi.types.chats import ChatMember
from maxapi.types.users import User

OWNER = {'user_id': 42, 'first_name': 'Женя', 'is_bot': False, 'last_activity_time': 1793125118000,
         'last_access_time': 1793125118000, 'is_owner': True, 'is_admin': True, 'join_time': 0}
# как в журнале сервера 29.10.2026: у удалённого аккаунта нет last_activity_time
DELETED = {'user_id': 7, 'first_name': 'DELETED USER', 'last_name': '', 'is_bot': False,
           'last_access_time': 0, 'is_owner': False, 'is_admin': True, 'join_time': 0,
           'name': 'DELETED USER'}
ADMINS = {'members': [OWNER, DELETED]}


@pytest.fixture
async def max_server():
    seen = []

    async def handler(request: web.Request):
        seen.append(request.path)
        return web.json_response(ADMINS)

    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    yield f'http://127.0.0.1:{runner.addresses[0][1]}', seen
    await runner.cleanup()


def test_user_and_member_without_last_activity_time():
    assert User(user_id=7, first_name='Гость', is_bot=False).last_activity_time is None
    member = ChatMember(**DELETED)
    assert (member.user_id, member.last_activity_time, member.is_admin) == (7, None, True)
    assert ChatMember(**OWNER).last_activity_time == 1793125118000


@pytest.mark.asyncio
async def test_admin_list_with_deleted_user_parses(max_server):
    url, seen = max_server
    bot = Bot(token='тест')
    bot.API_URL = url
    try:
        got = await bot.get_list_admin_chat(chat_id=-74907584209518)
    finally:
        await bot.close_session()
    assert seen == ['/chats/-74907584209518/members/admins']
    assert isinstance(got, GettedListAdminChat)
    assert [(m.user_id, m.last_activity_time) for m in got.members] == [(42, 1793125118000), (7, None)]


@pytest.mark.asyncio
async def test_event_sender_without_last_activity_time():
    event = {
        'update_type': 'message_created',
        'timestamp': 1759511800000,
        'message': {
            'sender': {'user_id': 7, 'first_name': 'Гость', 'is_bot': False},
            'recipient': {'chat_id': 1, 'chat_type': 'dialog'},
            'timestamp': 1759511800000,
            'body': {'mid': 'm1', 'seq': 1, 'text': '/start'},
        },
    }
    got = await process_update_request({'updates': [event]}, Bot(token='тест', auto_requests=False))
    assert isinstance(got[0], MessageCreated)
    assert got[0].message.sender.last_activity_time is None
