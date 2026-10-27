from __future__ import annotations
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .message import Recipient
from .users import User


class CommentMessageBody(BaseModel):

    """
    Тело комментария (спецификация MAX, `CommentMessageBody`).

    Нарочно без разметки и вложений: комментарий нужен боту как факт «кто
    и под каким постом», а незнакомый стиль разметки уронил бы разбор
    целой страницы комментариев.

    Attributes:
        mid (str): Идентификатор комментария.
        seq (Optional[int]): Порядковый номер.
        text (Optional[str]): Текст комментария.
    """

    mid: str
    seq: Optional[int] = None
    text: Optional[str] = None


class CommentMessage(BaseModel):

    """
    Комментарий к посту канала (спецификация MAX, `CommentMessage`).

    Attributes:
        sender (Optional[User]): Автор. None — комментарий от имени канала
            (так MAX публикует комментарии владельца канала, ТП24 28.10.2026).
        recipient (Recipient): Канал; `recipient.post_id` — пост.
        timestamp (int): Время создания, мс.
        link (Optional[Any]): Комментарий, на который ответили. Как есть:
            форма `CommentLinkedMessage` нам не нужна, а падать на ней нельзя.
        body (CommentMessageBody): Тело комментария.
    """

    sender: Optional[User] = None
    recipient: Recipient
    timestamp: int
    link: Optional[Any] = None
    body: CommentMessageBody
    bot: Optional[Any] = Field(default=None, exclude=True)


class Comments(BaseModel):

    """
    Страница комментариев `GET /messages/{messageId}/comments`.

    Attributes:
        messages (List[CommentMessage]): Комментарии.
    """

    messages: List[CommentMessage] = Field(default_factory=list)
    bot: Optional[Any] = Field(default=None, exclude=True)
