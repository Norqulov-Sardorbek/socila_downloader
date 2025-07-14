from bot.models import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.buttons.text import *

from bot.utils import remove_at_prefix
def join_channels():
    channels = ChannelsToSubscribe.objects.all()

    buttons = [
        [InlineKeyboardButton(
            text=channel.name,
            url=f"https://t.me/{remove_at_prefix(channel.link)}"
        )] for channel in channels
    ]

    buttons.append([InlineKeyboardButton(
        text="✅ Tasdiqlash",
        callback_data="check_subscription"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
