"""Догоняем платформу MAX (октябрь 2026): команды и новое событие.

Запуск из корня форка: `python -m pytest tests/ -q` (нужны pytest и
pytest-asyncio). Сеть не нужна — запросы уходят на локальный сервер-подмену.
"""

import logging

import pytest
from aiohttp import web

from maxapi import Bot, Dispatcher
from maxapi.enums.update import UpdateType
from maxapi.methods.types.getted_updates import process_update_request
from maxapi.types import BotAdminPermissionsChanged, MessageCreated
from maxapi.types.command import BotCommand, BotCommands


async def _fake_max():
    """Локальный «MAX»: запоминает каждый запрос и отвечает списком команд."""
    seen = []

    async def handler(request: web.Request):
        body = await request.json() if request.can_read_body else None
        seen.append({'method': request.method, 'path': request.path, 'body': body,
                     'auth': request.headers.get('Authorization')})
        return web.json_response({'commands': (body or {}).get('commands', [])})

    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    port = runner.addresses[0][1]
    return runner, f'http://127.0.0.1:{port}', seen


@pytest.fixture
async def max_server():
    runner, url, seen = await _fake_max()
    yield url, seen
    await runner.cleanup()


def _bot(url: str) -> Bot:
    bot = Bot(token='тест')
    bot.API_URL = url
    return bot


# --- 1. Команды: PATCH /me/commands -----------------------------------------

@pytest.mark.asyncio
async def test_set_my_commands_goes_to_me_commands_with_the_list(max_server):
    url, seen = max_server
    bot = _bot(url)
    try:
        result = await bot.set_my_commands(
            BotCommand(name='start', description='☰ Главное меню'),
            BotCommand(name='new', description='🎁 Создать розыгрыш'),
        )
    finally:
        await bot.close_session()

    assert seen == [{
        'method': 'PATCH',
        'path': '/me/commands',
        'body': {'commands': [
            {'name': 'start', 'description': '☰ Главное меню'},
            {'name': 'new', 'description': '🎁 Создать розыгрыш'},
        ]},
        'auth': None,
    }]
    assert isinstance(result, BotCommands)
    assert [c.name for c in result.commands] == ['start', 'new']


@pytest.mark.asyncio
async def test_empty_call_removes_all_commands(max_server):
    """Пустой массив — способ удалить все команды; его нельзя «не послать»."""
    url, seen = max_server
    bot = _bot(url)
    try:
        await bot.set_my_commands()
    finally:
        await bot.close_session()

    assert seen[0]['path'] == '/me/commands'
    assert seen[0]['body'] == {'commands': []}


# --- 2. bot_admin_permissions_changed ---------------------------------------

EVENT = {
    'update_type': 'bot_admin_permissions_changed',
    'timestamp': 1759511799000,
    'chat_id': -70000000000001,
    'user': {'user_id': 42, 'first_name': 'Женя', 'is_bot': False,
             'last_activity_time': 0},
    'is_channel': True,
    'permissions': ['write', 'edit_message'],
}

MESSAGE = {
    'update_type': 'message_created',
    'timestamp': 1759511800000,
    'message': {
        'sender': {'user_id': 7, 'first_name': 'Гость', 'is_bot': False,
                   'last_activity_time': 0},
        'recipient': {'chat_id': 1, 'chat_type': 'dialog'},
        'timestamp': 1759511800000,
        'body': {'mid': 'm1', 'seq': 1, 'text': '/start'},
    },
}


class _NoRequests:
    """Бот без запросов: разбор событий не должен ходить в сеть."""
    auto_requests = False


def test_the_event_type_is_known():
    assert UpdateType('bot_admin_permissions_changed') is UpdateType.BOT_ADMIN_PERMISSIONS_CHANGED


def test_the_model_keeps_unknown_fields_and_survives_missing_ones():
    event = BotAdminPermissionsChanged(**EVENT)
    assert event.get_ids() == (-70000000000001, 42)
    assert event.is_channel is True
    # Состав полей в документации не описан — пришедшее сверх модели не теряется.
    assert event.model_extra == {'permissions': ['write', 'edit_message']}

    bare = BotAdminPermissionsChanged(update_type='bot_admin_permissions_changed', timestamp=0)
    assert bare.get_ids() == (None, None)


def test_routers_can_subscribe_to_the_event():
    dp = Dispatcher()
    assert dp.bot_admin_permissions_changed.update_type is UpdateType.BOT_ADMIN_PERMISSIONS_CHANGED


@pytest.mark.asyncio
async def test_the_event_is_parsed_in_a_polling_batch():
    events = await process_update_request({'updates': [EVENT, MESSAGE]}, _NoRequests())
    assert [type(e) for e in events] == [BotAdminPermissionsChanged, MessageCreated]


@pytest.mark.asyncio
async def test_an_unknown_event_does_not_drop_the_rest_of_the_batch(caplog):
    """Живой лог 03.10.2026: незнакомое событие роняло всю пачку — вместе
    с сообщениями других людей."""
    future = {'update_type': 'something_from_2027', 'timestamp': 0}
    broken = {'update_type': 'message_created', 'timestamp': 0}  # без message

    with caplog.at_level(logging.WARNING, logger='dispatcher'):
        events = await process_update_request(
            {'updates': [future, broken, MESSAGE]}, _NoRequests(),
        )

    assert [type(e) for e in events] == [MessageCreated]
    text = caplog.text
    assert 'something_from_2027' in text
    assert 'message_created' in text
