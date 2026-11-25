"""Обработчики административных команд"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from .base_handler import BaseCommandHandler
from help_text import ADMIN_TEXT

logger = logging.getLogger(__name__)


class AdminCommands(BaseCommandHandler):
    """Обработчики административных команд"""
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /админ - административные функции"""
        try:
            
            user = update.effective_user
            logger.info(f"👤 Пользователь: {user.username if user else 'Неизвестный'}")
            
            # Убираем @ если он есть в admin_username
            admin_username_clean = self.bot.admin_username.lstrip('@')
            logger.info(f"👮 Требуется админ: {admin_username_clean}")
            
            if not user or user.username != admin_username_clean:
                logger.info(f"❌ Доступ запрещен для пользователя {user.username if user else 'аноним'}")
                await update.message.reply_text("❌ Эта команда доступна только администратору ассистента!")
                return
            
            logger.info("✅ Проверка прав пройдена")
            
            # Получаем статистику
            logger.info("📊 Получение статистики...")
            stats = self.bot.settings_manager.get_statistics()
            logger.info(f"📈 Статистика получена: {stats}")
            
            all_groups = self.bot.settings_manager.get_all_groups()
            logger.info(f"👥 Группы получены: {len(all_groups)}")
            
            # Считаем группы с и без уведомлений
            enabled_groups = stats['groups_with_notifications']
            disabled_groups = stats['total_groups'] - enabled_groups
            
            logger.info("📝 Форматирование текста...")
            admin_text = ADMIN_TEXT.format(
                total_groups=stats['total_groups'],
                enabled_groups=enabled_groups,
                disabled_groups=disabled_groups,
                congratulations_count=len(self.bot.congratulations)
            )
            
            logger.info("📤 Отправка сообщения...")
            logger.info(f"📝 Текст для отправки (первые 600 символов): {admin_text[:600]}")
            
            # Отправляем без Markdown форматирования
            await update.message.reply_text(admin_text)
            logger.info("✅ Команда /админ выполнена успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде /админ: {e}")
            
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке команды. Попробуйте повторить позже."
            )
    
    async def admin_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /админ список - список всех групп"""
        try:
            
            user = update.effective_user
            admin_username_clean = self.bot.admin_username.lstrip('@')
            
            if not user or user.username != admin_username_clean:
                await update.message.reply_text("❌ Эта команда доступна только администратору ассистента!")
                return
            
            # Получаем все группы
            all_groups = self.bot.settings_manager.get_all_groups()
            
            if not all_groups:
                await update.message.reply_text("❌ Нет зарегистрированных групп.")
                return
            
            # Формируем список групп
            message = "📋 *Список всех групп:*\n\n"
            
            for chat_id, group_data in all_groups.items():
                group_name = group_data.get('name', 'Без названия')
                notifications_enabled = group_data.get('notifications_enabled', False)
                notification_time = group_data.get('notification_time', '09:00')
                
                status = "🔔 ВКЛ" if notifications_enabled else "🔕 ВЫКЛ"
                message += f"• {group_name} (ID: {chat_id})\n  Статус: {status}, Время: {notification_time}\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info("✅ Команда /админ список выполнена успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде /админ список: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды.")
    
    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /админ статистика - подробная статистика"""
        try:
            
            user = update.effective_user
            admin_username_clean = self.bot.admin_username.lstrip('@')
            
            if not user or user.username != admin_username_clean:
                await update.message.reply_text("❌ Эта команда доступна только администратору ассистента!")
                return
            
            # Получаем подробную статистику
            stats = self.bot.settings_manager.get_statistics()
            all_groups = self.bot.settings_manager.get_all_groups()
            
            # Подсчитываем дополнительную информацию
            total_birthdays = 0
            total_weddings = 0
            total_events = 0
            
            for chat_id, group_data in all_groups.items():
                birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
                weddings = self.bot.settings_manager.get_weddings_for_group(chat_id)
                events = self.bot.settings_manager.get_events_for_group(chat_id)
                
                total_birthdays += len(birthdays) if birthdays else 0
                total_weddings += len(weddings) if weddings else 0
                total_events += len(events) if events else 0
            
            message = (
                f"📊 *Подробная статистика:*\n\n"
                f"👥 *Группы:*\n"
                f"• Всего групп: {stats['total_groups']}\n"
                f"• С уведомлениями: {stats['groups_with_notifications']}\n"
                f"• Без уведомлений: {stats['total_groups'] - stats['groups_with_notifications']}\n\n"
                f"🎂 *Дни рождения:*\n"
                f"• Всего записей: {total_birthdays}\n\n"
                f"💍 *Свадьбы:*\n"
                f"• Всего записей: {total_weddings}\n\n"
                f"📅 *События:*\n"
                f"• Всего записей: {total_events}\n\n"
                f"🎉 *Поздравления:*\n"
                f"• В базе: {len(self.bot.congratulations)} шт."
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info("✅ Команда /админ статистика выполнена успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде /админ статистика: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды.")
    
    async def admin_files_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /админ файлы - информация о файлах"""
        try:
            
            user = update.effective_user
            admin_username_clean = self.bot.admin_username.lstrip('@')
            
            if not user or user.username != admin_username_clean:
                await update.message.reply_text("❌ Эта команда доступна только администратору ассистента!")
                return
            
            # Получаем информацию о файлах
            import os
            groups_dir = "groups"
            
            if not os.path.exists(groups_dir):
                await update.message.reply_text("❌ Директория groups не найдена.")
                return
            
            files = os.listdir(groups_dir)
            json_files = [f for f in files if f.endswith('.json')]
            
            message = (
                f"📁 *Информация о файлах:*\n\n"
                f"📂 Директория: {groups_dir}\n"
                f"📄 JSON файлов: {len(json_files)}\n\n"
                f"📝 *Список файлов:*\n"
            )
            
            for filename in json_files[:10]:  # Показываем первые 10 файлов
                filepath = os.path.join(groups_dir, filename)
                size = os.path.getsize(filepath)
                message += f"• {filename} ({size} bytes)\n"
            
            if len(json_files) > 10:
                message += f"... и еще {len(json_files) - 10} файлов"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            logger.info("✅ Команда /админ файлы выполнена успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде /админ файлы: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды.")