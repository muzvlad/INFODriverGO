"""Модуль для обработки кнопок бота"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class ButtonHandlers:
    """Класс для обработки кнопок бота"""
    
    def __init__(self, main_bot):
        self.bot = main_bot
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = str(query.message.chat_id)
        
        if data == "enable_notifications":
            # Включаем уведомления
            self.bot.settings_manager.enable_notifications(chat_id)
            
            # Настраиваем планировщик
            if self.bot.application and self.bot.application.job_queue:
                self.bot.job_scheduler.setup_group_job(
                    chat_id, 
                    self.bot.settings_manager, 
                    self.bot.application.job_queue
                )
            
            await query.edit_message_text(
                "✅ Уведомления успешно включены!\n"
                "Теперь бот будет присылать уведомления о днях рождения."
            )
            
        elif data == "disable_notifications":
            # Выключаем уведомления
            self.bot.settings_manager.disable_notifications(chat_id)
            
            # Удаляем планировщик
            if chat_id in self.bot.job_scheduler.group_jobs:
                try:
                    self.bot.job_scheduler.group_jobs[chat_id].schedule_removal()
                    del self.bot.job_scheduler.group_jobs[chat_id]
                except:
                    pass
            
            await query.edit_message_text(
                "❌ Уведомления выключены.\n"
                "Бот больше не будет присылать уведомления о днях рождения."
            )
            
        elif data == "show_settings":
            # Показываем настройки
            notifications_enabled = self.bot.settings_manager.is_notifications_enabled(chat_id)
            notification_time = self.bot.settings_manager.get_notification_time(chat_id)
            
            settings_text = (
                f"⚙️ *Настройки уведомлений:*\n\n"
                f"🔔 Статус: {'включены ✅' if notifications_enabled else 'выключены ❌'}\n"
                f"⏰ Время: {notification_time.strftime('%H:%M')}\n\n"
                f"Используйте команды для изменения настроек:\n"
                f"• `/включить` - включить уведомления\n"
                f"• `/выключить` - выключить уведомления\n"
                f"• `/время ЧЧ:ММ` - изменить время"
            )
            
            await query.edit_message_text(settings_text, parse_mode='Markdown')
            
        elif data.startswith("set_time_"):
            # Установка времени
            time_part = data.split("_")[2]  # формат: set_time_HH:MM
            try:
                hour, minute = map(int, time_part.split(":"))
                
                # Устанавливаем новое время
                time_str = f"{hour:02d}:{minute:02d}"
                self.bot.settings_manager.set_notification_time(chat_id, time_str)
                
                # Обновляем планировщик
                self.bot.job_scheduler.update_group_job_time(chat_id, self.bot.settings_manager, self.bot.application)
                
                await query.edit_message_text(
                    f"✅ Время уведомлений установлено на {hour:02d}:{minute:02d}\n"
                    f"🔄 Изменения вступили в силу немедленно!"
                )
                
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Ошибка установки времени")
                
        elif data == "back_to_main":
            # Возвращаемся к главному меню
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton("⚙️ Настройки", callback_data="show_settings")],
                [
                    InlineKeyboardButton("✅ Включить", callback_data="enable_notifications"),
                    InlineKeyboardButton("❌ Выключить", callback_data="disable_notifications")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🎂 *Меню управления ботом дней рождения*\n\n"
                "Выберите действие:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )