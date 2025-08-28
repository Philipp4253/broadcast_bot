
import asyncio
from typing import List, Optional
from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, RetryAfter, UserDeactivated, CantInitiateConversation
from loguru import logger

class Broadcaster:
    def __init__(self, bot: Bot, delay_ms: int = 1200):
        self.bot = bot
        self.delay_ms = delay_ms

    def set_delay(self, delay_ms: int):
        self.delay_ms = max(0, delay_ms)

    async def send_text(self, user_ids: List[int], text: str, parse_mode: Optional[str] = None, media_file_id: Optional[str] = None):
        sent = 0
        failed = 0
        for uid in user_ids:
            try:
                if media_file_id:
                    await self.bot.send_photo(uid, media_file_id, caption=text, parse_mode=parse_mode)
                else:
                    await self.bot.send_message(uid, text, parse_mode=parse_mode)
                sent += 1
            except RetryAfter as e:
                wait = int(getattr(e, "timeout", 5)) + 1
                logger.warning(f"RetryAfter for {uid}: sleep {wait}s")
                await asyncio.sleep(wait)
                continue
            except (BotBlocked, ChatNotFound, UserDeactivated, CantInitiateConversation):
                failed += 1
            except Exception as e:
                logger.error(f"Send failed to {uid}: {e}")
                failed += 1
            await asyncio.sleep(self.delay_ms / 1000)
        return sent, failed
