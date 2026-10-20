from __future__ import annotations
from typing import Optional

from .update import Update

from ...types.message import Message


class CommentEdited(Update):

    """
    Обновление: комментарий к посту канала изменён (спецификация MAX,
    `CommentEditedUpdate`). Приходит, только если бот — админ канала с правом
    `read_all_messages`.

    Attributes:
        message (Message): Изменённый комментарий.
        user_locale (Optional[str]): Локаль пользователя.
    """

    message: Message
    user_locale: Optional[str] = None

    def get_ids(self):
        return (
            self.message.recipient.chat_id,
            self.message.sender.user_id if self.message.sender else None,
        )
