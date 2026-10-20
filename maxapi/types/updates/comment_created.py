from __future__ import annotations
from typing import Optional

from .update import Update

from ...types.message import Message


class CommentCreated(Update):

    """
    Обновление: создан комментарий к посту канала (спецификация MAX,
    `CommentCreatedUpdate`). Приходит, только если бот — админ канала с правом
    `read_all_messages`.

    Attributes:
        message (Message): Новый комментарий.
        user_locale (Optional[str]): Локаль пользователя.
    """

    message: Message
    user_locale: Optional[str] = None

    def get_ids(self):
        return (
            self.message.recipient.chat_id,
            self.message.sender.user_id if self.message.sender else None,
        )
