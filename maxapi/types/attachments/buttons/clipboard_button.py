from ....enums.button_type import ButtonType

from .button import Button


class ClipboardButton(Button):

    """
    Кнопка копирования текста в буфер обмена.

    Attributes:
        type: Тип кнопки (фиксированное значение ButtonType.CLIPBOARD)
        text: Текст, отображаемый на кнопке (наследуется от Button)
        payload: Текст, который копируется в буфер обмена при нажатии
    """

    type: ButtonType = ButtonType.CLIPBOARD
    payload: str
