"""Модуль для обработки уведомлений за 3 дня для личных сообщений"""
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ThreeDaysReminderMixin:
    """Миксин для уведомлений за 3 дня в личных сообщениях"""
    
    def _is_private_chat(self, chat_id: str) -> bool:
        """Проверяет, является ли чат личными сообщениями"""
        try:
            # Чаты с отрицательными ID - это группы/каналы
            # Чаты с положительными ID - это личные сообщения
            chat_id_int = int(chat_id)
            return chat_id_int > 0
        except ValueError:
            # Если не число, считаем группой
            return False
    
    def _calculate_three_days_before(self, target_date: datetime, notification_time) -> datetime:
        """Вычисляет дату за 3 дня до целевой даты"""
        # Целевая дата минус 3 дня
        three_days_before = target_date - timedelta(days=3)
        
        # Устанавливаем время уведомления из настроек группы
        three_days_reminder = datetime.combine(three_days_before.date(), notification_time)
        
        # Делаем timezone-aware
        if three_days_reminder.tzinfo is None and hasattr(target_date, 'tzinfo'):
            three_days_reminder = target_date.tzinfo.localize(three_days_reminder)
            
        return three_days_reminder
    
    def _setup_birthday_reminder(self, chat_id: str, name: str, birth_date: datetime, 
                               job_queue, timezone, notification_time):
        """Настраивает напоминание о дне рождения за 3 дня"""
        try:
            now = datetime.now(timezone)
            
            # Вычисляем дату напоминания
            reminder_date = self._calculate_three_days_before(birth_date, notification_time)
            
            # Отладочный лог
            logger.debug(f"🔍 Расчет напоминания для {name}: ДР={birth_date}, сейчас={now}, напоминание={reminder_date}, время={notification_time}")
            
            # Проверяем, что напоминание еще не прошло
            if reminder_date > now:
                seconds_until = (reminder_date - now).total_seconds()
                
                # Создаем одноразовое задание для напоминания
                job = job_queue.run_once(
                    self.send_birthday_reminder,
                    seconds_until,
                    data={
                        'chat_id': chat_id,
                        'name': name,
                        'birth_date': birth_date,
                        'reminder_type': 'birthday'
                    },
                    name=f"birthday_reminder_{chat_id}_{name}"
                )
                
                logger.info(f"✅ Настроено напоминание о дне рождения {name} за 3 дня "
                           f"(через {seconds_until:.0f} секунд)")
                return job
            else:
                logger.info(f"⏭️ Напоминание о дне рождения {name} уже прошло")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке напоминания о дне рождения {name}: {e}")
            return None
    
    def _setup_wedding_reminder(self, chat_id: str, name: str, wedding_date: datetime,
                              job_queue, timezone, notification_time):
        """Настраивает напоминание о свадьбе за 3 дня"""
        try:
            now = datetime.now(timezone)
            
            # Вычисляем дату напоминания
            reminder_date = self._calculate_three_days_before(wedding_date, notification_time)
            
            # Отладочный лог
            logger.debug(f"🔍 Расчет напоминания для {name}: Свадьба={wedding_date}, сейчас={now}, напоминание={reminder_date}, время={notification_time}")
            
            # Проверяем, что напоминание еще не прошло
            if reminder_date > now:
                seconds_until = (reminder_date - now).total_seconds()
                
                # Создаем одноразовое задание для напоминания
                job = job_queue.run_once(
                    self.send_wedding_reminder,
                    seconds_until,
                    data={
                        'chat_id': chat_id,
                        'name': name,
                        'wedding_date': wedding_date,
                        'reminder_type': 'wedding'
                    },
                    name=f"wedding_reminder_{chat_id}_{name}"
                )
                
                logger.info(f"✅ Настроено напоминание о свадьбе {name} за 3 дня "
                           f"(через {seconds_until:.0f} секунд)")
                return job
            else:
                logger.info(f"⏭️ Напоминание о свадьбе {name} уже прошло")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке напоминания о свадьбе {name}: {e}")
            return None
    
    async def send_birthday_reminder(self, context):
        """Отправляет напоминание о дне рождения за 3 дня"""
        try:
            chat_id = context.job.data.get('chat_id')
            name = context.job.data.get('name')
            birth_date = context.job.data.get('birth_date')
            
            if not chat_id or not name or not birth_date:
                logger.error("❌ Не хватает данных для отправки напоминания о дне рождения")
                return
            
            # Получаем бота из контекста
            bot = self._get_main_bot(context)
            if not bot:
                logger.error("❌ Основной бот не найден для отправки напоминания")
                return
            
            # Получаем реального Telegram бота
            telegram_bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'bot')):
                telegram_bot = context.application.bot
            elif hasattr(context, 'bot'):
                telegram_bot = context.bot
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для напоминаний")
                return
            
            # Создаем фейковый контекст
            class FakeContext:
                def __init__(self, telegram_bot_instance, job_data):
                    self.bot = telegram_bot_instance
                    self.job = type('FakeJob', (), {'data': job_data})()
                    self.application = type('FakeApplication', (), {'bot': telegram_bot_instance})()
            
            fake_context = FakeContext(telegram_bot, context.job.data)
            
            # Форматируем дату рождения текстом
            months = [
                '', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
            ]
            birth_date_formatted = f"{birth_date.day} {months[birth_date.month]}"
            
            # Отправляем напоминание
            message = f"🔔 Напоминание: Через 3 дня день рождения у {name} ({birth_date_formatted})!"
            await telegram_bot.send_message(chat_id=chat_id, text=message)
            
            logger.info(f"✅ Отправлено напоминание о дне рождения {name} в личные сообщения {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке напоминания о дне рождения {name}: {e}")
    
    async def send_wedding_reminder(self, context):
        """Отправляет напоминание о свадьбе за 3 дня"""
        try:
            chat_id = context.job.data.get('chat_id')
            name = context.job.data.get('name')
            wedding_date = context.job.data.get('wedding_date')
            
            if not chat_id or not name or not wedding_date:
                logger.error("❌ Не хватает данных для отправки напоминания о свадьбе")
                return
            
            # Получаем бота из контекста
            bot = self._get_main_bot(context)
            if not bot:
                logger.error("❌ Основной бот не найден для отправки напоминания")
                return
            
            # Получаем реального Telegram бота
            telegram_bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'bot')):
                telegram_bot = context.application.bot
            elif hasattr(context, 'bot'):
                telegram_bot = context.bot
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для напоминаний")
                return
            
            # Создаем фейковый контекст
            class FakeContext:
                def __init__(self, telegram_bot_instance, job_data):
                    self.bot = telegram_bot_instance
                    self.job = type('FakeJob', (), {'data': job_data})()
                    self.application = type('FakeApplication', (), {'bot': telegram_bot_instance})()
            
            fake_context = FakeContext(telegram_bot, context.job.data)
            
            # Форматируем дату свадьбы текстом
            months = [
                '', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
            ]
            wedding_date_formatted = f"{wedding_date.day} {months[wedding_date.month]}"
            
            # Отправляем напоминание
            message = f"🔔 Напоминание: Через 3 дня годовщина свадьбы у {name} ({wedding_date_formatted})!"
            await telegram_bot.send_message(chat_id=chat_id, text=message)
            
            logger.info(f"✅ Отправлено напоминание о свадьбе {name} в личные сообщения {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке напоминания о свадьбе {name}: {e}")
    
    def setup_three_days_reminders(self, chat_id: str, settings_manager, job_queue, timezone):
        """Настраивает все напоминания за 3 дня для личных сообщений"""
        try:
            chat_id_str = str(chat_id)
            
            # Проверяем, что это личные сообщения
            if not self._is_private_chat(chat_id_str):
                logger.info(f"⏭️ Пропускаем напоминания за 3 дня для группы {chat_id_str}")
                return
            
            logger.info(f"🔔 Настройка напоминаний за 3 дня для личных сообщений {chat_id_str}")
            
            # Получаем время уведомлений
            notification_time = settings_manager.get_notification_time(chat_id_str)
            
            # Настраиваем напоминания о днях рождения
            birthdays = settings_manager.get_birthdays_for_group(chat_id_str)
            if birthdays:
                for name_key, data in birthdays.items():
                    try:
                        name = data['name']
                        day = int(data['day'])
                        month = int(data['month'])
                        year = data.get('year')
                        
                        # Создаем дату рождения в этом году
                        now = datetime.now(timezone)
                        if year:
                            birth_date = timezone.localize(datetime(now.year, month, day))
                            # Если день рождения уже прошел в этом году, ставим на следующий год
                            if birth_date < now:
                                birth_date = timezone.localize(datetime(now.year + 1, month, day))
                        else:
                            birth_date = timezone.localize(datetime(now.year, month, day))
                            if birth_date < now:
                                birth_date = timezone.localize(datetime(now.year + 1, month, day))
                        
                        # Настраиваем напоминание
                        self._setup_birthday_reminder(
                            chat_id_str, name, birth_date, job_queue, timezone, notification_time
                        )
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка при настройке напоминания о дне рождения {name_key}: {e}")
            
            # Настраиваем напоминания о свадьбах
            weddings = settings_manager.get_weddings_for_group(chat_id_str)
            if weddings:
                for name_key, data in weddings.items():
                    try:
                        name = data['name']
                        day = int(data['day'])
                        month = int(data['month'])
                        year = data.get('year')
                        
                        # Создаем дату свадьбы в этом году
                        now = datetime.now(timezone)
                        if year:
                            wedding_date = timezone.localize(datetime(now.year, month, day))
                            # Если годовщина уже прошла в этом году, ставим на следующий год
                            if wedding_date < now:
                                wedding_date = timezone.localize(datetime(now.year + 1, month, day))
                        else:
                            wedding_date = timezone.localize(datetime(now.year, month, day))
                            if wedding_date < now:
                                wedding_date = timezone.localize(datetime(now.year + 1, month, day))
                        
                        # Настраиваем напоминание
                        self._setup_wedding_reminder(
                            chat_id_str, name, wedding_date, job_queue, timezone, notification_time
                        )
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка при настройке напоминания о свадьбе {name_key}: {e}")
            
            logger.info(f"✅ Настройка напоминаний за 3 дня завершена для {chat_id_str}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке напоминаний за 3 дня для {chat_id}: {e}")