from aiogram.utils.keyboard import InlineKeyboardBuilder

def payment_keyboard(amount: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить {amount} ⭐️", pay=True)
    return builder.as_markup()