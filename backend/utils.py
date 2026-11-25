"""Утилиты для общих операций"""
import logging

logger = logging.getLogger(__name__)


def validate_chat_id(context, function_name: str) -> str:
    """
    Проверяет и возвращает chat_id из контекста
    
    Args:
        context: Контекст выполнения
        function_name: Имя функции для логирования
        
    Returns:
        str: chat_id если найден
        
    Raises:
        ValueError: Если chat_id не найден
    """
    chat_id = context.job.data.get('chat_id') if hasattr(context.job, 'data') else None
    if not chat_id:
        logger.error(f"❌ Не указан chat_id для {function_name}")
        if hasattr(context, 'job'):
            logger.error(f"❌ Доступные атрибуты context.job: {dir(context.job)}")
        raise ValueError(f"chat_id не найден для {function_name}")
    
    logger.info(f"🔔 Начинаем выполнение {function_name} для группы {chat_id}")
    return chat_id


def get_bot_from_context(context):
    """
    Получает бота из контекста различными способами
    
    Args:
        context: Контекст выполнения
        
    Returns:
        Бот или None если не найден
    """
    bot = None
    
    # Способ 1: Через application.main_bot
    if (hasattr(context, 'application') and 
        hasattr(context.application, 'main_bot')):
        bot = context.application.main_bot
        logger.info("✅ Найден main_bot через context.application.main_bot")
    
    # Способ 2: Через application.bot.main_bot
    elif (hasattr(context, 'application') and 
          hasattr(context.application, 'bot') and 
          hasattr(context.application.bot, 'main_bot')):
        bot = context.application.bot.main_bot
        logger.info("✅ Найден main_bot через context.application.bot.main_bot")
        
    # Способ 3: Проверка атрибутов
    elif hasattr(context, 'bot'):
        logger.warning("⚠️ Найден ExtBot через context.bot, но нужен BirthdayBot")
        if hasattr(context, 'application') and 'main_bot' in dir(context.application):
            bot = context.application.main_bot
            logger.info("✅ Найден main_bot через проверку атрибутов")
    
    if not bot:
        logger.error("❌ BirthdayBot не найден в контексте")
    
    return bot