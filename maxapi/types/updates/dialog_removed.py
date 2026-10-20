from typing import TYPE_CHECKING, Optional

from .update import Update

from ...types.users import User

if TYPE_CHECKING:
    from ...bot import Bot


class DialogRemoved(Update):

    """
    Обновление: диалог с ботом удалён (спецификация MAX, `DialogRemovedUpdate`).

    Attributes:
        chat_id (int): Идентификатор диалога.
        user (User): Кто удалил диалог.
        user_locale (Optional[str]): Локаль пользователя.
    """

    chat_id: int
    user: User
    user_locale: Optional[str] = None

    if TYPE_CHECKING:
        bot: Optional[Bot]

    def get_ids(self):
        return (self.chat_id, self.user.user_id)
