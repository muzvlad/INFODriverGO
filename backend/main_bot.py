#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной класс бота для дней рождения
"""

import logging
from telegram.ext import Application
from config import config
from backend.command_handlers.command_handlers import CommandHandlers
from backend.button_handlers import ButtonHandlers
from backend.file_manager import FileManager
from backend.group_manager import GroupManager
from backend.scheduler import UnifiedJobScheduler as JobScheduler
from backend.settings_manager import AllSettings

logger = logging.getLogger(__name__)

class MainBot:
    """Основной класс бота для управления уведомлениями"""
    
    def __init__(self):
        self.bot_token = config.BOT_TOKEN
        self.timezone = config.TIMEZONE
        self.admin_username = "muzvlad911"  # Можно сделать настраиваемым
        
        # Инициализируем менеджеры
        self.file_manager = FileManager()
        self.group_manager = GroupManager()
        self.settings_manager = AllSettings()  # Создаем менеджер настроек
        
        # Инициализируем планировщик с часовым поясом
        import pytz
        timezone_obj = pytz.timezone(self.timezone)
        self.job_scheduler = JobScheduler(timezone_obj, self.settings_manager)
        # Передаем ссылку на себя в планировщик
        self.job_scheduler._bot_ref = self
        
        # Загружаем данные
        self.congratulations = self.file_manager.load_congratulations()
        self.birthdays = self.file_manager.load_all_groups()
        self.group_names_cache = self.group_manager.load_group_names_cache(self.settings_manager)
        
        # Инициализируем обработчики
        self.command_handlers = CommandHandlers(self)
        self.button_handlers = ButtonHandlers(self)
        
        self.application = None
    
    async def delete_message_later(self, context, chat_id, message_id, delay=5):
        """Удаляет сообщение через заданное количество секунд"""
        try:
            # Ждем заданное количество секунд
            import asyncio
            await asyncio.sleep(delay)
            
            # Удаляем сообщение
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении сообщения {message_id} в чате {chat_id}: {e}")
    
    def run(self):
        """Запускает бота через BotRunner"""
        from backend.bot_runner import BotRunner
        runner = BotRunner(self)
        runner.run()
    
    # Методы команд (делегируем CommandHandlers)
    def start_command(self, update, context):
        return self.command_handlers.start_command(update, context)
    
    def help_command(self, update, context):
        return self.command_handlers.help_command(update, context)
    
    def settings_command(self, update, context):
        return self.command_handlers.settings_command(update, context)
    
    def status_command(self, update, context):
        return self.command_handlers.status_command(update, context)
    
    def add_birthday(self, update, context):
        return self.command_handlers.add_birthday(update, context)
    
    def list_birthdays(self, update, context):
        return self.command_handlers.list_birthdays(update, context)
    
    def delete_birthday(self, update, context):
        return self.command_handlers.delete_birthday(update, context)
    
    def today_birthdays(self, update, context):
        return self.command_handlers.today_birthdays(update, context)
    
    def upcoming_birthdays(self, update, context):
        return self.command_handlers.upcoming_birthdays(update, context)
    
    # Методы работы со свадьбами
    def add_wedding(self, update, context):
        return self.command_handlers.add_wedding(update, context)
    
    def list_weddings(self, update, context):
        return self.command_handlers.list_weddings(update, context)
    
    def delete_wedding(self, update, context):
        return self.command_handlers.delete_wedding(update, context)
    
    # Методы работы с событиями
    def add_event(self, update, context):
        return self.command_handlers.add_event(update, context)
    
    def list_events(self, update, context):
        return self.command_handlers.list_events(update, context)
    
    def delete_event(self, update, context):
        return self.command_handlers.delete_event(update, context)
    
    def enable_notifications(self, update, context):
        return self.command_handlers.enable_notifications(update, context)
    
    def disable_notifications(self, update, context):
        return self.command_handlers.disable_notifications(update, context)
    
    def set_notification_time(self, update, context):
        return self.command_handlers.set_notification_time(update, context)
    
    def admin_command(self, update, context):
        return self.command_handlers.admin_command(update, context)
    
    def handle_russian_command(self, update, context):
        return self.command_handlers.handle_russian_command(update, context)
    
    # Методы кнопок (делегируем ButtonHandlers)
    def button_callback(self, update, context):
        return self.button_handlers.button_callback(update, context)
    
    async def send_group_notification(self, context):
        """Отправляет уведомление о днях рождения в группу"""
        try:
            from datetime import datetime
            import random
            

            from backend.utils import validate_chat_id
            try:
                chat_id = validate_chat_id(context, "уведомления")
            except ValueError:
                return
            
            # Проверяем, включены ли уведомления для этой группы
            if not self.settings_manager.is_notifications_enabled(chat_id):
                logger.info(f"🔕 Уведомления выключены для группы {chat_id}")
                return
            
            # Получаем дни рождения и свадьбы на сегодня
            today = datetime.now()
            logger.info(f"📅 Проверяем дни рождения и свадьбы на {today.strftime('%d.%m.%Y')}")
            
            # Получаем дни рождения для конкретной группы
            birthdays = self.settings_manager.get_birthdays_for_group(chat_id)
            today_birthdays = []
            
            if birthdays:
                today_day = today.day
                today_month = today.month
                
                for name, date_info in birthdays.items():
                    day = int(date_info['day'])
                    month = int(date_info['month'])
                    
                    if day == today_day and month == today_month:
                        today_birthdays.append({'name': name, 'type': 'birthday'})
                        logger.info(f"🎂 Найден именинник: {name}")
            
            # Получаем свадьбы для конкретной группы
            weddings = self.settings_manager.get_weddings_for_group(chat_id)
            today_weddings = []
            
            if weddings:
                today_day = today.day
                today_month = today.month
                
                for name_key, wedding_data in weddings.items():
                    day = int(wedding_data['day'])
                    month = int(wedding_data['month'])
                    name = wedding_data['name']
                    
                    if day == today_day and month == today_month:
                        today_weddings.append({'name': name, 'type': 'wedding'})
                        logger.info(f"💍 Найдена годовщина свадьбы: {name}")
            
            # Если нет ни дней рождения, ни свадеб
            if not today_birthdays and not today_weddings:
                logger.info(f"📅 Нет дней рождения и свадеб сегодня в группе {chat_id}")
                return
            
            # Отправляем поздравления отдельно: сначала дни рождения, потом свадьбы
            
            # Отправляем поздравления с днями рождения
            if today_birthdays:
                if len(today_birthdays) == 1:
                    person = today_birthdays[0]
                    birthday_message = f"🎉 Сегодня день рождения у {person['name']}! 🎂\n\n"
                    logger.info(f"🎉 Отправляем поздравление с днем рождения: {person['name']}")
                else:
                    names = ", ".join([p['name'] for p in today_birthdays])
                    birthday_message = f"🎉 Сегодня дни рождения у: {names}! 🎂\n\n"
                    logger.info(f"🎉 Отправляем поздравление с несколькими днями рождения: {names}")
                
                # Добавляем поздравление из файла congratulations
                if self.congratulations and len(self.congratulations) > 0:
                    congratulation = random.choice(self.congratulations)
                    birthday_message += f"🎊 {congratulation}"
                    logger.info(f"🎊 Добавлено поздравление из файла: {congratulation[:30]}...")
                else:
                    birthday_message += "🎊 С днем рождения! 🎈"
                    logger.info("🎊 Использовано стандартное поздравление")
                
                # Отправляем поздравление с днем рождения
                await context.bot.send_message(chat_id=chat_id, text=birthday_message)
                logger.info(f"✅ Поздравление с днем рождения отправлено в группу {chat_id}")
                
                # Небольшая пауза между сообщениями
                import asyncio
                await asyncio.sleep(2)
            
            # Отправляем поздравления со свадьбами
            if today_weddings:
                # Загружаем свадебные поздравления
                wedding_congratulations = self.file_manager.load_weddings()
                
                if len(today_weddings) == 1:
                    wedding = today_weddings[0]
                    wedding_message = f"🎉 Сегодня годовщина свадьбы у {wedding['name']}! 💍\n\n"
                    logger.info(f"🎉 Отправляем поздравление со свадьбой: {wedding['name']}")
                else:
                    names = ", ".join([p['name'] for p in today_weddings])
                    wedding_message = f"🎉 Сегодня годовщины свадеб у: {names}! 💍\n\n"
                    logger.info(f"🎉 Отправляем поздравление с несколькими свадьбами: {names}")
                
                # Добавляем поздравление из файла weddings
                if wedding_congratulations and len(wedding_congratulations) > 0:
                    congratulation = random.choice(wedding_congratulations)
                    wedding_message += f"🎊 {congratulation}"
                    logger.info(f"🎊 Добавлено свадебное поздравление: {congratulation[:30]}...")
                else:
                    wedding_message += "🎊 С юбилеем свадьбы! 💝"
                    logger.info("🎊 Использовано стандартное свадебное поздравление")
                
                # Отправляем поздравление со свадьбой
                await context.bot.send_message(chat_id=chat_id, text=wedding_message)
                logger.info(f"✅ Поздравление со свадьбой отправлено в группу {chat_id}")
                
                # Небольшая пауза между сообщениями
                import asyncio
                await asyncio.sleep(2)
            
            # События отправляются отдельно через планировщик событий
            # Здесь их не отправляем, чтобы избежать дублирования
            
            # Если ничего не было отправлено
            if not today_birthdays and not today_weddings:
                logger.info(f"📅 Нет дней рождения и свадеб сегодня в группе {chat_id}")
                return
            
            logger.info(f"✅ Уведомления успешно отправлены в группу {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления в группу {chat_id}: {e}")
    
    async def send_event_notification(self, context):
        """Отправляет уведомление о событии"""
        try:
            from datetime import datetime
            
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            event_type = context.job.data.get('event_type')
            
            if not chat_id or not event_name:
                logger.error("❌ Не хватает данных для отправки уведомления о событии")
                return
            
            logger.info(f"🔔 Отправляем уведомление о событии '{event_name}' в группу {chat_id}")
            
            # Проверяем, есть ли текст события в данных контекста
            event_text = context.job.data.get('event_text')
            
            if not event_text:
                # Если текста нет в контексте, загружаем из файла events.json
                events_data = self.file_manager.load_events()
                
                # Ищем текст по ключу события (регистронезависимо)
                event_key_lower = event_name.lower()
                event_text = events_data.get(event_key_lower)
                
                # Если не нашли, пробуем оригинальный регистр
                if not event_text:
                    event_text = events_data.get(event_name)
                
                # Если всё равно не нашли, используем стандартный текст
                if not event_text:
                    event_text = f"{event_name} начинается!"
                else:
                    # Извлекаем текст из структуры {"text": "..."}
                    if isinstance(event_text, dict) and 'text' in event_text:
                        event_text = event_text['text']
            
            logger.info(f"📅 Текст события '{event_name}': {event_text}")
            
            # Формируем сообщение
            message = f"{event_text}"
            
            # Получаем реального Telegram бота
            telegram_bot = self._get_telegram_bot(context)
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для отправки сообщения")
                return
            
            # Для игровых событий добавляем повтор через 2 минуты
            gaming_events = ['td', 'ea', 'ew']  # Защита, Элитные приключения, Элитная война
            if event_name.lower() in gaming_events:
                # Отправляем основное сообщение
                await telegram_bot.send_message(chat_id=chat_id, text=message)
                logger.info(f"✅ Основное уведомление о событии '{event_name}' отправлено")
                
                # Планируем повтор через 2 минуты
                if context.application and context.application.job_queue:
                    context.application.job_queue.run_once(
                        self.send_repeat_notification,
                        120,  # 2 минуты
                        data={'chat_id': chat_id, 'event_name': event_name},
                        name=f"repeat_{chat_id}_{event_name}_{int(datetime.now().timestamp())}"
                    )
                    logger.info(f"⏰ Запланирован повтор для события '{event_name}' через 2 минуты")
            else:
                # Отправляем обычное сообщение
                await telegram_bot.send_message(chat_id=chat_id, text=message)
                logger.info(f"✅ Уведомление о событии '{event_name}' отправлено")
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о событии '{event_name}': {e}")
    
    async def send_repeat_notification(self, context):
        """Отправляет повторное уведомление"""
        try:
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            
            if not chat_id or not event_name:
                logger.error("❌ Не хватает данных для отправки повторного уведомления")
                return
            
            # Загружаем события из файла
            events_data = self.file_manager.load_events()
            
            # Получаем текст повтора (регистронезависимо)
            repeat_text = events_data.get('repeat', "⚔️🛡Го го го!")
            if repeat_text == "⚔️🛡Го го го!":
                repeat_text = events_data.get('Repeat', repeat_text)
            
            logger.info(f"📅 Текст повтора: {repeat_text}")
            
            # Получаем реального Telegram бота через универсальный метод
            telegram_bot = self._get_telegram_bot(context)
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для отправки повторного уведомления")
                return
            
            # Отправляем повторное уведомление
            await telegram_bot.send_message(chat_id=chat_id, text=repeat_text)
            logger.info(f"✅ Повторное уведомление для события '{event_name}' отправлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки повторного уведомления: {e}")
    
    async def send_wedding_notification(self, context):
        """Отправляет уведомление о годовщине свадьбы"""
        try:
            import random
            from datetime import datetime
            
            chat_id = context.job.data.get('chat_id')
            wedding_name = context.job.data.get('wedding_name')
            
            if not chat_id or not wedding_name:
                logger.error("❌ Не хватает данных для отправки уведомления о свадьбе")
                return
            
            logger.info(f"💍 Отправляем уведомление о годовщине свадьбы '{wedding_name}' в группу {chat_id}")
            
            # Загружаем свадебные поздравления
            wedding_congratulations = self.file_manager.load_weddings()
            
            # Формируем сообщение
            message = f"🎉 Сегодня годовщина свадьбы у {wedding_name}! 💍\n\n"
            
            # Добавляем поздравление
            if wedding_congratulations and len(wedding_congratulations) > 0:
                congratulation = random.choice(wedding_congratulations)
                message += f"🎊 {congratulation}"
            else:
                message += "🎊 С юбилеем свадьбы! 💝"
            
            # Получаем реального Telegram бота через универсальный метод
            telegram_bot = self._get_telegram_bot(context)
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для отправки уведомления о свадьбе")
                return
            
            # Отправляем сообщение
            await telegram_bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"✅ Уведомление о годовщине свадьбы '{wedding_name}' отправлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о свадьбе '{wedding_name}': {e}")
    
    def _get_telegram_bot(self, context):
        """Универсальный метод для получения Telegram бота из контекста"""
        try:
            # Приоритет 1: Через application.main_bot
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'main_bot') and
                hasattr(context.application.main_bot, 'application') and
                hasattr(context.application.main_bot.application, 'bot')):
                return context.application.main_bot.application.bot
            
            # Приоритет 2: Через application.bot
            elif (hasattr(context, 'application') and 
                  hasattr(context.application, 'bot')):
                return context.application.bot
            
            # Приоритет 3: Прямой доступ
            elif hasattr(context, 'bot'):
                return context.bot
            
            # Приоритет 4: Через self.application
            elif (hasattr(self, 'application') and 
                  hasattr(self.application, 'bot')):
                return self.application.bot
            
            logger.error("❌ Не удалось получить Telegram бота из контекста")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении Telegram бота: {e}")
            return None