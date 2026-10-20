"""Новые типы событий MAX по спецификации (github.com/max-messenger/api-schema,
21.10.2026): comment_created, comment_edited, comment_removed, dialog_removed.

Раньше незнакомый тип в вебхуке падал `ValueError: Unknown update type`, в
long polling — пропускался строкой в логе. Теперь все четыре разбираются и
доходят до своих обработчиков диспетчера. Сеть не нужна.
"""

from types import SimpleNamespace

import pytest

from maxapi import Dispatcher
from maxapi.enums.update import UpdateType
from maxapi.methods.types.getted_updates import process_update_request, process_update_webhook
from maxapi.types import CommentCreated, CommentEdited, CommentRemoved, DialogRemoved

BOT = SimpleNamespace(auto_requests=False)
USER = {"user_id": 5, "first_name": "Гость", "is_bot": False, "last_activity_time": 0}
COMMENT = {
    "sender": USER,
    "recipient": {"chat_id": -100, "chat_type": "channel"},
    "timestamp": 1,
    "body": {"mid": "mid-comment", "seq": 1, "text": "отличный розыгрыш", "attachments": []},
}


def _events():
    return [
        {"update_type": "comment_created", "timestamp": 1, "message": COMMENT},
        {"update_type": "comment_edited", "timestamp": 2, "message": COMMENT},
        {"update_type": "comment_removed", "timestamp": 3,
         "message_id": "mid-comment", "chat_id": -100, "user_id": 5, "post_id": "mid-post"},
        {"update_type": "dialog_removed", "timestamp": 4, "chat_id": 77, "user": USER},
    ]


def test_enum_has_new_types():
    assert {t.value for t in UpdateType} >= {
        "comment_created", "comment_edited", "comment_removed", "dialog_removed",
    }


@pytest.mark.asyncio
async def test_webhook_parses_each_new_type():
    kinds = [type(await process_update_webhook(e, BOT)) for e in _events()]
    assert kinds == [CommentCreated, CommentEdited, CommentRemoved, DialogRemoved]


@pytest.mark.asyncio
async def test_polling_batch_keeps_new_types():
    got = await process_update_request({"updates": _events()}, BOT)
    assert [type(e) for e in got] == [CommentCreated, CommentEdited, CommentRemoved, DialogRemoved]
    removed = got[2]
    assert (removed.post_id, removed.get_ids()) == ("mid-post", (-100, 5))
    assert got[3].get_ids() == (77, 5)
    assert got[0].get_ids() == (-100, 5)


def test_dispatcher_has_handlers_for_new_types():
    dp = Dispatcher()
    for name in ("comment_created", "comment_edited", "comment_removed", "dialog_removed"):
        assert getattr(dp, name).update_type == UpdateType(name)
