from typing import TYPE_CHECKING, List, Optional

from ..types.comment import Comments
from ..enums.http_method import HTTPMethod
from ..enums.api_path import ApiPath
from ..connection.base import BaseConnection


if TYPE_CHECKING:
    from ..bot import Bot


class GetComments(BaseConnection):

    """
    Комментарии к посту канала: `GET /messages/{messageId}/comments`.

    Бот должен быть админом канала с правом `read_all_messages`. Маркера
    следующей страницы MAX не отдаёт: листать — окнами `after` / `before`
    (мс, обе границы включительно — ТП24 28.10.2026).

    Args:
        bot (Bot): Экземпляр бота.
        message_id (str): Идентификатор поста (`mid`).
        count (int): Сколько комментариев вернуть, 1–100. По умолчанию 100.
        after (int, optional): Время в мс, начиная с которого.
        before (int, optional): Время в мс, до которого.
        comment_ids (List[str], optional): Только эти комментарии
            (удалённые в ответ не попадают); окна и `count` MAX тогда
            не учитывает.
    """

    def __init__(
            self,
            bot: 'Bot',
            message_id: str,
            count: int = 100,
            after: Optional[int] = None,
            before: Optional[int] = None,
            comment_ids: Optional[List[str]] = None,
        ):
        self.bot = bot
        self.message_id = message_id
        self.count = count
        self.after = after
        self.before = before
        self.comment_ids = comment_ids

    async def fetch(self) -> Comments:

        if self.bot is None:
            raise RuntimeError('Bot не инициализирован')

        params = self.bot.params.copy()

        if self.comment_ids:
            params['comment_ids'] = ','.join(self.comment_ids)
        else:
            params['count'] = self.count
            if self.after is not None:
                params['after'] = self.after
            if self.before is not None:
                params['before'] = self.before

        return await super().request(
            method=HTTPMethod.GET,
            path=f'{ApiPath.MESSAGES.value}/{self.message_id}/comments',
            model=Comments,
            params=params
        )
