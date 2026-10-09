from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict

from .update import Update

from ...types.users import User

if TYPE_CHECKING:
    from ...bot import Bot
    

class BotAdminPermissionsChanged(Update):
    
    """
    Обновление, сигнализирующее об изменении прав бота-администратора
    в канале или групповом чате (MAX, октябрь 2026).

    Документация обещает событие только через Webhook, но 03.10.2026 оно
    пришло и в long polling. Состав полей в документации не описан —
    поэтому все поля необязательные, а незнакомые сохраняются
    (`extra='allow'`): событие не должно падать на разборе, а что в нём
    пришло, видно в `model_extra`.

    Attributes:
        chat_id (Optional[int]): Идентификатор канала или чата.
        user (Optional[User]): Пользователь, изменивший права.
        is_channel (Optional[bool]): Канал это или групповой чат.
    """

    model_config = ConfigDict(extra='allow')
    
    chat_id: Optional[int] = None
    user: Optional[User] = None
    is_channel: Optional[bool] = None
    
    if TYPE_CHECKING:
        bot: Optional[Bot]

    def get_ids(self):
        return (self.chat_id, self.user.user_id if self.user else None)
