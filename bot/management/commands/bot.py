import asyncio
import logging
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
from django.core.management import BaseCommand
from bot.handlers import *
from dispatcher import TOKEN, dp
from aiogram.client.default import DefaultBotProperties
# Set the default settings module for your Django project
async def main() -> None:
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)



class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
