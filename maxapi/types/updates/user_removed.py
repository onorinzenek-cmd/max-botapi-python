from typing import Optional

from .update import Update

from ...types.users import User


class UserRemoved(Update):
    
    """
    Класс для обработки события выходе/удаления пользователя из чата.

    Attributes:
        admin_id (Optional[int]): Идентификатор администратора, удалившего пользователя. None при выходе из чата самим пользователем.
        chat_id (int): Идентификатор чата. Может быть None.
        user (User): Объект пользователя, удаленного из чата.
        is_channel (bool): Указывает, был ли пользователь удален из канала или нет
    """
    
    admin_id: Optional[int] = None
    chat_id: int
    user: User
    is_channel: bool
    
    def get_ids(self):
        
        """
        Возвращает кортеж идентификаторов (chat_id, user_id).

        user_id — это ВЫШЕДШИЙ/удалённый (self.user), а не admin_id: тот же
        класс бага, что был у MessageEdited.get_ids() — брался инициатор
        события вместо его героя. При самостоятельном выходе admin_id вовсе
        None, и get_ids возвращал (chat_id, None). Кто удалил — по-прежнему
        доступен в поле admin_id.

        Returns:
            Tuple[Optional[int], Optional[int]]: Идентификаторы чата и пользователя.
        """
        
        return (self.chat_id, self.user.user_id)