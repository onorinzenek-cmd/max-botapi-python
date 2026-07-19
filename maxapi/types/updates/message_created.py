from __future__ import annotations
from typing import Optional

from .update import Update

from ...types.message import Message


class MessageCreated(Update):
    
    """
    Обновление, сигнализирующее о создании нового сообщения.

    Attributes:
        message (Message): Объект сообщения.
        user_locale (Optional[str]): Локаль пользователя.
    """
    
    message: Message
    user_locale: Optional[str] = None
    
    def get_ids(self):

        """
        Возвращает кортеж идентификаторов (chat_id, user_id).

        У постов канала (сообщение от имени канала, не от человека) sender
        отсутствует — тогда user_id вернётся None.

        Returns:
            tuple[Optional[int], Optional[int]]: Идентификатор чата и пользователя.
        """

        return (
            self.message.recipient.chat_id,
            self.message.sender.user_id if self.message.sender else None,
        )