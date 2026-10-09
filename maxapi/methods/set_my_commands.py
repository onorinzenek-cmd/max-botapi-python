from typing import TYPE_CHECKING, List

from ..types.command import BotCommand, BotCommands

from ..enums.http_method import HTTPMethod
from ..enums.api_path import ApiPath

from ..connection.base import BaseConnection


if TYPE_CHECKING:
    from ..bot import Bot


class SetMyCommands(BaseConnection):
    
    """
    Класс для установки списка команд бота (подсказки при вводе «/»).

    С сентября 2026 MAX принимает команды только отдельным методом
    `PATCH /me/commands`; старый путь — поле `commands` в `PATCH /me` —
    отвечает 404 `Path /me is not recognized`.
    https://dev.max.ru/docs-api/methods/PATCH/me/commands

    Args:
        bot (Bot): Экземпляр бота для выполнения запроса.
        commands (List[BotCommand]): Список команд, до 32 штук.
            Пустой список удаляет все команды.
    """
    
    def __init__(self, bot: 'Bot', commands: List[BotCommand]):
        self.bot = bot
        self.commands = commands

    async def fetch(self) -> BotCommands:
        
        """
        Выполняет PATCH-запрос для установки команд бота.

        Returns:
            BotCommands: Команды, которые теперь поддерживает бот.
        """
        
        if self.bot is None:
            raise RuntimeError('Bot не инициализирован')
        
        # Список уходит ВСЕГДА, даже пустой: пустой массив — это способ
        # удалить все команды, а не «ничего не менять».
        return await super().request(
            method=HTTPMethod.PATCH, 
            path=ApiPath.ME_COMMANDS,
            model=BotCommands,
            params=self.bot.params,
            json={'commands': [command.model_dump() for command in self.commands]}
        )
