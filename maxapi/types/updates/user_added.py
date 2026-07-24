from typing import Optional

from .update import Update

from ...types.users import User


class UserAdded(Update):
    
    """
    Класс для обработки события добавления пользователя в чат.

    Attributes:
        inviter_id (int): Идентификатор пользователя, добавившего нового участника. Может быть None.
        chat_id (int): Идентификатор чата. Может быть None.
        user (User): Объект пользователя, добавленного в чат.
        is_channel (bool): Указывает, был ли пользователь добавлен в канал или нет
    """
    
    inviter_id: Optional[int] = None
    chat_id: int
    user: User
    is_channel: bool
    
    def get_ids(self):
        
        """
        Возвращает кортеж идентификаторов (chat_id, user_id).

        user_id — это ВСТУПИВШИЙ (self.user), а не inviter_id: тот же класс
        бага, что был у MessageEdited.get_ids() — брался инициатор события
        вместо его героя. При самоподписке inviter_id вовсе None (человек
        вступил сам), и get_ids возвращал (chat_id, None). Кто добавил —
        по-прежнему доступен в поле inviter_id.

        Returns:
            Tuple[Optional[int], Optional[int]]: Идентификаторы чата и пользователя.
        """
        
        return (self.chat_id, self.user.user_id)