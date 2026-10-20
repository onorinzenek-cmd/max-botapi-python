from .update import Update


class CommentRemoved(Update):

    """
    Обновление: комментарий к посту канала удалён (спецификация MAX,
    `CommentRemovedUpdate`).

    Attributes:
        message_id (str): Идентификатор удалённого комментария.
        chat_id (int): Чат, где удалён комментарий.
        user_id (int): Кто удалил.
        post_id (str): Идентификатор поста.
    """

    message_id: str
    chat_id: int
    user_id: int
    post_id: str

    def get_ids(self):
        return (self.chat_id, self.user_id)
