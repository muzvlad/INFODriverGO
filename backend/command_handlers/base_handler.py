"""Базовый класс для обработчиков команд"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BaseCommandHandler:
    """Базовый класс для всех обработчиков команд"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Базовый метод обработки команды"""
        raise NotImplementedError("Метод handle_command должен быть реализован в подклассе")