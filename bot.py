"""Telegram bot that sends messages to telegram channel."""

import asyncio
import argparse
import logging
import requests
import yaml

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description="Run Telegram bot with config")
parser.add_argument(
    '--config',
    type=str,
    default='./default.yaml',
    help='Path to config YAML file'
)
args = parser.parse_args()


def load_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = load_config(args.config)['config']

bot = Bot(token=config['Telegram']['token'])
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Handles the /start command.
    """
    await message.answer(
        'Бот активен!'
    )
    logging.info("New user: %s", message.from_user.username)


async def send_message(text: str, report_id: int):
    await bot.send_message(
        chat_id=config['Telegram']['admin_id'],
        text=text,
    )
    response = requests.put(
        f"https://{config['api']['host']}:{config['api']['port']}/change_status",
        json={
            "report_id": report_id,
            "status": "closed",
        }
    )
    if response.status_code != 200:
        logging.error("Failed to change status")
        await bot.send_message(
            chat_id=config['Telegram']['admin_id'],
            text=f'Ошибка при обновлении статуса у заявки с id {report_id}',
        )


async def main():
    """
    Main entry point to start the bot.
    Includes the router and starts polling.
    """
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
