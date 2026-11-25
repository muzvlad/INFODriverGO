"""Обработчики команд статуса"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .base_handler import BaseCommandHandler
from .user_commands import UserCommands
from .admin_commands import AdminCommands
from .birthday_commands import BirthdayCommands
from .wedding_commands import WeddingCommands
from .event_commands import EventCommands

logger = logging.getLogger(__name__)


class StatusHandlers(BaseCommandHandler):
    """Обработчики команд статуса"""
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды статуса (общий для /status и /статус)"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Получаем настройки
        notifications_enabled = self.bot.settings_manager.is_notifications_enabled(chat_id)
        notification_time = self.bot.settings_manager.get_notification_time(chat_id)
        
        # Получаем статистику
        stats = self.bot.settings_manager.get_statistics()
        
        # Получаем количество дней рождений в этой группе
        birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
        birthdays_count = len(birthdays) if birthdays else 0
        
        # Получаем количество свадеб в этой группе
        weddings = self.bot.settings_manager.get_weddings_for_group(chat_id)
        weddings_count = len(weddings) if weddings else 0
        
        # Получаем количество событий в этой группе
        events = self.bot.settings_manager.get_events_for_group(chat_id)
        events_count = len(events) if events else 0
        
        # Формируем текст статуса
        status_text = (
            f"📊 *Статус бота в этой группе:*\n\n"
            f"🔔 Уведомления: {'включены ✅' if notifications_enabled else 'выключены ❌'}\n"
            f"⏰ Время уведомлений: {notification_time.strftime('%H:%M')}\n"
            f"👥 Всего групп: {stats['total_groups']}\n\n"
        )
        
        # Добавляем информацию о днях рождения
        status_text += f"🎂 Дни рождения: {birthdays_count} человек\n"
        
        # Добавляем информацию о свадьбах
        status_text += f"💍 Свадьбы: {weddings_count} человек с установленным временем уведомлений\n"
        
        # Добавляем информацию о событиях
        status_text += f"📅 События: {events_count} шт. с установленным временем уведомлений\n"
        
        # Если есть события, показываем их
        if events:
            status_text += "\n📝 *Активные события:*\n"
            for event_name, event_data in events.items():
                event_type = event_data.get('type', 'неизвестно')
                event_time = event_data.get('time', 'неизвестно')
                status_text += f"  • {event_data.get('name', event_name)} - {event_type} в {event_time}\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_russian_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка русских команд через MessageHandler"""
        if not update.message or not update.message.text:
            return
            
        original_text = update.message.text.strip()
        text_lower = original_text.lower()
        logger.info(f"📥 Получено сообщение: '{original_text}'")
        
        # Проверяем, является ли это командой
        if not original_text.startswith('/'):
            logger.info("💬 Это обычное сообщение, не команда")
            return
            
        logger.info(f"📥 Получена команда: {original_text}")
        
        # Определяем команду
        if text_lower.startswith("/старт"):
            logger.info("🔄 Выполняется команда /старт")
            user_commands = UserCommands(self.bot)
            return await user_commands.start_command(update, context)
        elif text_lower.startswith("/справка"):
            logger.info("🔄 Выполняется команда /справка")
            user_commands = UserCommands(self.bot)
            return await user_commands.help_command(update, context)
        elif text_lower.startswith("/настройки"):
            logger.info("🔄 Выполняется команда /настройки")
            user_commands = UserCommands(self.bot)
            return await user_commands.settings_command(update, context)
        elif text_lower.startswith("/статус"):
            logger.info("🔄 Выполняется команда /статус")
            status_commands = StatusHandlers(self.bot)
            return await status_commands.status_command(update, context)
        elif text_lower.startswith("/админ список"):
            logger.info("🔄 Выполняется команда /админ список")
            admin_commands = AdminCommands(self.bot)
            return await admin_commands.admin_list_command(update, context)
        elif text_lower.startswith("/админ статистика"):
            logger.info("🔄 Выполняется команда /админ статистика")
            admin_commands = AdminCommands(self.bot)
            return await admin_commands.admin_stats_command(update, context)
        elif text_lower.startswith("/админ файлы"):
            logger.info("🔄 Выполняется команда /админ файлы")
            admin_commands = AdminCommands(self.bot)
            return await admin_commands.admin_files_command(update, context)
        elif text_lower == "/админ":  # Только точное совпадение для базовой команды
            logger.info("🔄 Выполняется команда /админ")
            admin_commands = AdminCommands(self.bot)
            return await admin_commands.admin_command(update, context)
        elif text_lower.startswith("/включить"):
            logger.info("🔄 Выполняется команда /включить")
            user_commands = UserCommands(self.bot)
            return await user_commands.enable_notifications(update, context)
        elif text_lower.startswith("/выключить"):
            logger.info("🔄 Выполняется команда /выключить")
            user_commands = UserCommands(self.bot)
            return await user_commands.disable_notifications(update, context)
        elif text_lower.startswith("/время "):
            logger.info("🔄 Выполняется команда /время")
            user_commands = UserCommands(self.bot)
            return await user_commands.set_notification_time(update, context)
        elif text_lower.startswith("/добавить "):
            logger.info("🔄 Выполняется команда /добавить")
            birthday_commands = BirthdayCommands(self.bot)
            return await birthday_commands.add_birthday_command(update, context)
        elif text_lower.startswith("/список"):
            logger.info("🔄 Выполняется команда /список")
            birthday_commands = BirthdayCommands(self.bot)
            return await birthday_commands.list_birthdays_command(update, context)
        elif text_lower.startswith("/удалить"):
            logger.info("🔄 Выполняется команда /удалить")
            birthday_commands = BirthdayCommands(self.bot)
            return await birthday_commands.delete_birthday_command(update, context)

        elif text_lower.startswith("/сегодня"):
            logger.info("🔄 Выполняется команда /сегодня")
            birthday_commands = BirthdayCommands(self.bot)
            return await birthday_commands.today_birthdays_command(update, context)
        elif text_lower.startswith("/ближайшие"):
            logger.info("🔄 Выполняется команда /ближайшие")
            birthday_commands = BirthdayCommands(self.bot)
            return await birthday_commands.upcoming_birthdays_command(update, context)
        
        # === СВАДЕБНЫЕ КОМАНДЫ ===
        elif text_lower.startswith("/свадьба "):
            wedding_commands = WeddingCommands(self.bot)
            return await wedding_commands.add_wedding_command(update, context)
        elif text_lower.startswith("/свадьбы"):
            wedding_commands = WeddingCommands(self.bot)
            return await wedding_commands.list_weddings_command(update, context)
        elif text_lower.startswith("/несвадьба "):
            wedding_commands = WeddingCommands(self.bot)
            return await wedding_commands.delete_wedding_command(update, context)


        
        # === СОБЫТИЙНЫЕ КОМАНДЫ ===
        elif text_lower.startswith("/событие "):
            event_commands = EventCommands(self.bot)
            return await event_commands.add_event_command(update, context)
        elif text_lower.startswith("/события"):
            event_commands = EventCommands(self.bot)
            return await event_commands.list_events_command(update, context)
        elif text_lower.startswith("/несобытие "):
            event_commands = EventCommands(self.bot)
            return await event_commands.delete_event_command(update, context)


        else:
            logger.info(f"❓ Неизвестная команда: {original_text}")
            # Если команда не распознана
            await update.message.reply_text(
                "❌ Неизвестная команда!\n"
                "Введите /справка для списка доступных команд."
            )


