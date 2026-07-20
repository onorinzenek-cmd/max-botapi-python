from .update import Update

from ...types.message import Message


class MessageEdited(Update):
    
    """
    Обновление, сигнализирующее об изменении сообщения.

    Attributes:
        message (Message): Объект измененного сообщения.
    """
    
    message: Message
    
    def get_ids(self):

        """
        Возвращает кортеж идентификаторов (chat_id, user_id).

        В личном диалоге message.recipient — это ПОЛУЧАТЕЛЬ сообщения (сам бот),
        а не автор правки. Берём id автора из sender — как это уже делает
        MessageCreated.get_ids() — иначе FSM-контекст ищется под user_id бота,
        а не человека, и состояние мастера никогда не находится.

        Returns:
            Tuple[Optional[int], Optional[int]]: Идентификаторы чата и пользователя.
        """

        return (
            self.message.recipient.chat_id,
            self.message.sender.user_id if self.message.sender else None,
        )