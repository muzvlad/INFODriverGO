"""Обработчики команд для обычных пользователей"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .base_handler import BaseCommandHandler
from help_text import HELP_TEXT, START_TEXT, SETTINGS_TEXT

logger = logging.getLogger(__name__)


class UserCommands(BaseCommandHandler):
    """Обработчики команд для обычных пользователей"""
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        
        user = update.effective_user
        chat = update.effective_chat
        
        # Обновляем информацию о группе
        self.bot.group_manager.update_group_info_from_chat(update, self.bot.settings_manager)
        
        # Формируем приветственное сообщение
        if chat.type == 'private':
            welcome_text = f"Привет, {user.first_name}! 👋\n\n"
        else:
            welcome_text = f"Привет всем в группе {chat.title}! 👋\n\n"
        
        full_text = welcome_text + START_TEXT
        
        await update.message.reply_text(full_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help - отправка справки блоками"""
        
        # Обновляем информацию о группе
        self.bot.group_manager.update_group_info_from_chat(update, self.bot.settings_manager)
        
        # Разбиваем HELP_TEXT на блоки
        blocks = self._split_help_text_into_blocks()
        
        # Отправляем каждый блок с задержкой
        for i, block in enumerate(blocks):
            await update.message.reply_text(block, parse_mode='Markdown')
            # Делаем паузу между блоками (кроме последнего)
            if i < len(blocks) - 1:
                import asyncio
                await asyncio.sleep(2)
    
    def _split_help_text_into_blocks(self):
        """Разбивает текст справки на логические блоки"""
        # Импортируем HELP_TEXT
        from help_text import HELP_TEXT
        
        # Разбиваем по пустым строкам и формируем блоки
        lines = HELP_TEXT.strip().split('\n')
        blocks = []
        current_block = []
        
        for line in lines:
            if line.strip() == '' and current_block:
                # Пустая строка - завершаем блок
                blocks.append('\n'.join(current_block))
                current_block = []
            elif line.strip():
                current_block.append(line)
        
        # Добавляем последний блок если он есть
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # Фильтруем пустые блоки
        blocks = [block for block in blocks if block.strip()]
        
        return blocks
    
    def _translate_chat_type(self, chat_type: str) -> str:
        """Переводит тип чата на русский язык"""
        translations = {
            'private': 'личный чат',
            'group': 'группа',
            'supergroup': 'супергруппа',
            'channel': 'канал'
        }
        return translations.get(chat_type.lower(), chat_type)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings"""
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Обновляем информацию о группе
        self.bot.group_manager.update_group_info_from_chat(update, self.bot.settings_manager)
        
        # Получаем настройки
        notifications_enabled = self.bot.settings_manager.is_notifications_enabled(chat_id)
        notification_time = self.bot.settings_manager.get_notification_time(chat_id)
        
        # Получаем дополнительную информацию
        group_info = self.bot.settings_manager.get_group_info(chat_id)
        group_name = self.bot.group_manager.get_group_name(chat_id)
        birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
        stats = self.bot.settings_manager.get_statistics()
        
        # Формируем текст настроек
        settings_text = (
            f"⚙️ *НАСТРОЙКИ АССИСТЕНТА*\n\n"
            f"*📋 Информация о чате:*\n"
            f"• ID чата: `{chat_id}`\n"
            f"• Название: {group_name}\n"
            f"• Тип: {self._translate_chat_type(chat.type)}\n\n"
            f"*🔔 Уведомления:*\n"
            f"• Статус: {'включены ✅' if notifications_enabled else 'выключены ❌'}\n"
            f"• Время: {notification_time.strftime('%H:%M')}\n"
            f"• Часовой пояс: Europe/Moscow\n\n"
            f"*📊 Статистика:*\n"
            f"• Дней рождения в этой группе: {len(birthdays)}\n"
            f"• Всего групп в ассистенте: {stats['total_groups']}\n"
            f"• Групп с уведомлениями: {stats['groups_with_notifications']}\n\n"
            f"*👑 Администратор:* @{self.bot.admin_username}\n\n"
            f"*ℹ️ Команды управления:* `/справка`"
        )
        
        await update.message.reply_text(settings_text, parse_mode='Markdown')
    
    async def enable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включить уведомления"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        self.bot.settings_manager.enable_notifications(chat_id)
        
        # Настраиваем планировщик
        if (hasattr(self.bot, 'application') and 
            self.bot.application and 
            hasattr(self.bot.application, 'job_queue') and 
            self.bot.application.job_queue):
            try:
                self.bot.job_scheduler.setup_group_job(
                    chat_id, 
                    self.bot.settings_manager, 
                    self.bot.application.job_queue
                )
            except Exception as e:
                logger.warning(f"Не удалось настроить планировщик для группы {chat_id}: {e}")
        
        await update.message.reply_text("✅ Уведомления включены!")
    
    async def disable_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выключить уведомления"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        self.bot.settings_manager.disable_notifications(chat_id)
        
        # Удаляем планировщик
        if (hasattr(self.bot, 'job_scheduler') and 
            hasattr(self.bot.job_scheduler, 'group_jobs') and
            chat_id in self.bot.job_scheduler.group_jobs):
            try:
                self.bot.job_scheduler.group_jobs[chat_id].schedule_removal()
                del self.bot.job_scheduler.group_jobs[chat_id]
            except Exception as e:
                logger.warning(f"Не удалось удалить планировщик для группы {chat_id}: {e}")
        
        await update.message.reply_text("❌ Уведомления выключены!")
    
    async def set_notification_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установить время уведомлений"""
        from datetime import datetime
        import pytz
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split()
        
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
                "Используйте: `/время ЧЧ:ММ`\n"
                "Например: `/время 09:00`"
            )
            return
        
        time_str = parts[1]
        
        # Проверяем формат времени
        if ':' not in time_str or len(time_str) != 5:
            await update.message.reply_text(
                "❌ Неверный формат времени!\n"
                "Используйте формат ЧЧ:ММ\n"
                "Например: `09:00` или `23:30`"
            )
            return
        
        # Устанавливаем время
        if not self.bot.settings_manager.set_notification_time(chat_id, time_str):
            await update.message.reply_text("❌ Неверное время! Используйте формат 00:00 - 23:59")
            return
        
        # Получаем установленное время
        notification_time = self.bot.settings_manager.get_notification_time(chat_id)
        
        # Проверяем текущее время
        timezone = pytz.timezone(self.bot.timezone)
        now = datetime.now(timezone)
        
        # Создаем время уведомлений сегодня
        today_notification_naive = datetime.combine(now.date(), notification_time)
        today_notification = timezone.localize(today_notification_naive)
        
        # Обновляем планировщик
        if (hasattr(self.bot, 'application') and 
            self.bot.application and 
            hasattr(self.bot.application, 'job_queue') and 
            self.bot.application.job_queue):
            
            try:
                # Обновляем время уведомлений с проверкой сегодняшнего дня
                self.bot.job_scheduler.update_group_job_time(
                    chat_id, 
                    self.bot.settings_manager, 
                    self.bot.application
                )
                
                # Проверяем, нужно ли отправить уведомление сегодня
                if today_notification > now:
                    # Время еще не прошло сегодня - отправим уведомление
                    await update.message.reply_text(
                        f"✅ Время уведомлений установлено на {time_str}\n"
                        f"🎉 Уведомления с поздравлениями будут отправляться в {time_str} 🎂"
                    )
                else:
                    # Время уже прошло - уведомление будет завтра
                    await update.message.reply_text(
                        f"✅ Время уведомлений установлено на {time_str}\n"
                        f"📅 Уведомление будет отправлено завтра в {time_str} 🎂"
                    )
            except Exception as e:
                logger.warning(f"Не удалось обновить планировщик для группы {chat_id}: {e}")
                await update.message.reply_text(f"✅ Время уведомлений установлено на {time_str}")
        else:
            await update.message.reply_text(f"✅ Время уведомлений установлено на {time_str}")