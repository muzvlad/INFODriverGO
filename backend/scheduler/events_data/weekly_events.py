"""Модуль для работы с недельными событиями (еженедельные и двухнедельные)"""
import logging
from datetime import datetime, timedelta, time
import pytz

logger = logging.getLogger(__name__)


class WeeklyEventsMixin:
    """Миксин для работы с недельными событиями"""
    
    def _setup_weekly_event(self, chat_id: str, event_name: str, time_str: str, job_queue, timezone, event_text: str):
        """Настраивает еженедельное событие"""
        try:
            # Парсим день недели и время из time_str (формат: "день_время")
            day_part, time_part = time_str.split('_', 1)
            hour, minute = map(int, time_part.split(':'))
            
            # Определяем номер дня недели
            day_numbers = {
                'понедельник': 0, 'monday': 0,
                'вторник': 1, 'tuesday': 1,
                'среда': 2, 'wednesday': 2,
                'четверг': 3, 'thursday': 3,
                'пятница': 4, 'friday': 4,
                'суббота': 5, 'saturday': 5,
                'воскресенье': 6, 'sunday': 6
            }
            
            target_weekday = day_numbers.get(day_part.lower(), 5)  # по умолчанию суббота
            
            # Создаем timezone-aware время для следующего нужного дня
            now = datetime.now(timezone)
            event_time = time(hour, minute)
            
            # Создаем дату события на сегодня
            today_event = timezone.localize(
                datetime.combine(now.date(), event_time)
            )
            
            # Если сегодня нужный день недели и время еще не прошло - событие сегодня
            if now.weekday() == target_weekday and today_event > now:
                # Событие сегодня
                scheduled_time = today_event
                logger.info(f"✅ Еженедельное событие '{event_name}' запланировано на сегодня: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                # Находим следующий нужный день недели
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:  # Цель или прошедшее воскресенье
                    days_ahead += 7
                
                next_weekday = now + timedelta(days=days_ahead)
                scheduled_time = timezone.localize(
                    datetime.combine(next_weekday.date(), event_time)
                )
            
            logger.info(f"🕒 Планируем еженедельное событие '{event_name}' на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone.zone})")
            
            # Используем run_once с автоматическим перепланированием для постоянного еженедельного повторения
            seconds_until = (scheduled_time - now).total_seconds()
            
            # Для еженедельных событий создаем отдельный метод, как для двухнедельных
            job = job_queue.run_once(
                self._send_weekly_event_notification,
                seconds_until,
                data={
                    'chat_id': chat_id, 
                    'event_name': event_name, 
                    'event_type': 'еженедельно',
                    'event_text': event_text,
                    'next_run_time': time(hour, minute),  # Сохраняем время для следующего запуска
                    'target_weekday': target_weekday  # Сохраняем день недели
                },
                name=f"weekly_event_{chat_id}_{event_name}"
            )
            
            logger.info(f"✅ Настроено еженедельное событие '{event_name}' на {day_part} в {time_part} ({timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке еженедельного события '{event_name}': {e}")
    
    def _setup_biweekly_event(self, chat_id: str, event_name: str, time_str: str, job_queue, timezone, event_text: str):
        """Настраивает событие раз в 2 недели"""
        try:
            # Парсим день недели и время из time_str (формат: "день_время")
            day_part, time_part = time_str.split('_', 1)
            hour, minute = map(int, time_part.split(':'))
            
            # Определяем номер дня недели
            day_numbers = {
                'понедельник': 0, 'monday': 0,
                'вторник': 1, 'tuesday': 1,
                'среда': 2, 'wednesday': 2,
                'четверг': 3, 'thursday': 3,
                'пятница': 4, 'friday': 4,
                'суббота': 5, 'saturday': 5,
                'воскресенье': 6, 'sunday': 6
            }
            
            target_weekday = day_numbers.get(day_part.lower(), 5)  # по умолчанию суббота
            
            # Получаем текущую дату в часовом поясе бота
            now = datetime.now(timezone)
            event_time = time(hour, minute)
            
            # Создаем дату события на сегодня
            today_event = timezone.localize(
                datetime.combine(now.date(), event_time)
            )
            
            # Если сегодня нужный день недели и время еще не прошло - событие сегодня
            if now.weekday() == target_weekday and today_event > now:
                # Событие сегодня
                seconds_until = (today_event - now).total_seconds()
                logger.info(f"✅ Событие раз в 2 недели '{event_name}' запланировано на сегодня через {seconds_until:.0f} секунд")
                
                job = job_queue.run_once(
                    self.send_biweekly_event_notification,
                    seconds_until,
                    data={
                        'chat_id': chat_id, 
                        'event_name': event_name, 
                        'event_time': time_str,
                        'event_text': event_text,
                        'target_weekday': target_weekday
                    },
                    name=f"biweekly_event_{chat_id}_{event_name}_today"
                )
                
            else:
                # Находим следующий нужный день недели
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7  # следующая неделя
                
                # Для двухнедельного события добавляем еще 7 дней, если сегодня не нужный день
                # или если сегодня нужный день, но время уже прошло
                if now.weekday() != target_weekday or today_event <= now:
                    days_ahead += 7
                
                next_biweekly = now + timedelta(days=days_ahead)
                next_biweekly = next_biweekly.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # next_biweekly уже timezone-aware, так как создан из now с timezone
                # localize не нужен
                
                seconds_until = (next_biweekly - now).total_seconds()
                
                logger.info(f"🕒 Планируем событие раз в 2 недели '{event_name}' на {next_biweekly.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone.zone})")
                
                job = job_queue.run_once(
                    self.send_biweekly_event_notification,
                    seconds_until,
                    data={
                        'chat_id': chat_id, 
                        'event_name': event_name, 
                        'event_time': time_str,
                        'event_text': event_text,
                        'target_weekday': target_weekday
                    },
                    name=f"biweekly_event_{chat_id}_{event_name}"
                )
            
            logger.info(f"✅ Настроено событие раз в 2 недели '{event_name}' через {seconds_until:.0f} секунд ({timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке события раз в 2 недели '{event_name}': {e}")
    
    async def send_biweekly_event_notification(self, context):
        """Отправляет уведомление о событии раз в 2 недели и настраивает следующее"""
        try:
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            event_time = context.job.data.get('event_time')
            
            if not chat_id or not event_name or not event_time:
                logger.error("❌ Не хватает данных для отправки уведомления о событии раз в 2 недели")
                return
            
            # Получаем бота из контекста
            bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'main_bot')):
                bot = context.application.main_bot
                logger.info("✅ Найден main_bot через context.application.main_bot")
            
            elif (hasattr(context, 'application') and 
                  hasattr(context.application, 'bot') and 
                  hasattr(context.application.bot, 'main_bot')):
                bot = context.application.bot.main_bot
                logger.info("✅ Найден main_bot через context.application.bot.main_bot")
                
            elif hasattr(context, 'bot'):
                logger.warning("⚠️ Найден ExtBot через context.bot, но нужен BirthdayBot")
                if hasattr(context, 'application'):
                    if 'main_bot' in dir(context.application):
                        bot = context.application.main_bot
                        logger.info("✅ Найден main_bot через проверку атрибутов")
            
            if not bot:
                logger.error("❌ BirthdayBot не найден в контексте")
                return
            
            # Получаем реального Telegram бота
            telegram_bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'bot')):
                telegram_bot = context.application.bot
            elif hasattr(context, 'bot'):
                telegram_bot = context.bot
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота")
                return
            
            # Создаем фейковый контекст с реальным Telegram ботом
            # ВАЖНО: Не добавляем main_bot в application, чтобы избежать рекурсии
            class FakeContext:
                def __init__(self, telegram_bot_instance, job_data):
                    self.bot = telegram_bot_instance
                    self.job = type('FakeJob', (), {'data': job_data})()
                    # Создаем application без main_bot, чтобы _get_telegram_bot не пытался получить MainBot
                    self.application = type('FakeApplication', (), {
                        'bot': telegram_bot_instance,
                        # Не добавляем main_bot!
                    })()
            
            fake_context = FakeContext(telegram_bot, context.job.data)
            
            # Отправляем уведомление
            await bot.send_event_notification(fake_context)
            logger.info(f"✅ Уведомление о событии раз в 2 недели '{event_name}' отправлено в группу {chat_id}")
            
            # Настраиваем следующее событие через 2 недели
            if context.application and context.application.job_queue:
                day_part, time_part = event_time.split('_', 1)
                hour, minute = map(int, time_part.split(':'))
                
                day_numbers = {
                    'понедельник': 0, 'monday': 0,
                    'вторник': 1, 'tuesday': 1,
                    'среда': 2, 'wednesday': 2,
                    'четверг': 3, 'thursday': 3,
                    'пятница': 4, 'friday': 4,
                    'суббота': 5, 'saturday': 5,
                    'воскресенье': 6, 'sunday': 6
                }
                
                target_weekday = day_numbers.get(day_part.lower(), 5)
                
                import pytz
                from config import config
                timezone = pytz.timezone(config.TIMEZONE)
                now = datetime.now(timezone)
                
                days_ahead = target_weekday - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                days_ahead += 7
                
                next_biweekly = now + timedelta(days=days_ahead)
                next_biweekly = next_biweekly.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # next_biweekly уже timezone-aware, так как now имеет timezone
                # Проверка tzinfo не нужна
                
                seconds_until = (next_biweekly - now).total_seconds()
                
                # Получаем текст события из контекста или файла
                event_text = context.job.data.get('event_text')
                if not event_text:
                    # Если текста нет в контексте, загружаем из файла events.json
                    from backend.file_manager import FileManager
                    file_manager = FileManager()
                    events_data = file_manager.load_events()
                    
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
                
                context.application.job_queue.run_once(
                    self.send_biweekly_event_notification,
                    seconds_until,
                    data={
                        'chat_id': chat_id,
                        'event_name': event_name,
                        'event_time': event_time,
                        'event_text': event_text
                    },
                    name=f"biweekly_event_{chat_id}_{event_name}"
                )
                logger.info(f"✅ Следующее событие раз в 2 недели '{event_name}' настроено через {seconds_until:.0f} секунд")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправки уведомления о событии раз в 2 недели '{event_name}': {e}")
    
    async def _send_weekly_event_notification(self, context):
        """Отправляет уведомление о еженедельном событии с правильным контекстом"""
        try:
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            event_type = context.job.data.get('event_type')
            event_text = context.job.data.get('event_text')
            
            if not chat_id or not event_name:
                logger.error("❌ Не хватает данных для отправки уведомления о еженедельном событии")
                return
            
            # Получаем бота из контекста
            bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'main_bot')):
                bot = context.application.main_bot
                logger.info("✅ Найден main_bot через context.application.main_bot")
            
            elif (hasattr(context, 'application') and 
                  hasattr(context.application, 'bot') and 
                  hasattr(context.application.bot, 'main_bot')):
                bot = context.application.bot.main_bot
                logger.info("✅ Найден main_bot через context.application.bot.main_bot")
                
            elif hasattr(context, 'bot'):
                logger.warning("⚠️ Найден ExtBot через context.bot, но нужен BirthdayBot")
                if hasattr(context, 'application'):
                    if 'main_bot' in dir(context.application):
                        bot = context.application.main_bot
                        logger.info("✅ Найден main_bot через проверку атрибутов")
            
            if not bot:
                logger.error("❌ BirthdayBot не найден в контексте")
                return
            
            # Получаем реального Telegram бота
            telegram_bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'bot')):
                telegram_bot = context.application.bot
            elif hasattr(context, 'bot'):
                telegram_bot = context.bot
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота")
                return
            
            # Создаем фейковый контекст с реальным Telegram ботом
            # ВАЖНО: Не добавляем main_bot в application, чтобы избежать рекурсии
            class FakeContext:
                def __init__(self, telegram_bot_instance, job_data):
                    self.bot = telegram_bot_instance
                    self.job = type('FakeJob', (), {'data': job_data})()
                    # Создаем application без main_bot, чтобы _get_telegram_bot не пытался получить MainBot
                    self.application = type('FakeApplication', (), {
                        'bot': telegram_bot_instance,
                        # Не добавляем main_bot!
                    })()
            
            fake_context = FakeContext(telegram_bot, context.job.data)
            
            # Отправляем уведомление
            await bot.send_event_notification(fake_context)
            logger.info(f"✅ Уведомление о еженедельном событии '{event_name}' отправлено в группу {chat_id}")
            
            # Настраиваем следующее событие через неделю
            if context.application and context.application.job_queue:
                # Получаем исходные данные
                event_type = context.job.data.get('event_type', 'еженедельно')
                target_weekday = context.job.data.get('target_weekday', 5)  # по умолчанию суббота
                next_run_time = context.job.data.get('next_run_time')
                
                if next_run_time:
                    import pytz
                    from config import config
                    timezone = pytz.timezone(config.TIMEZONE)
                    now = datetime.now(timezone)
                    
                    # Находим следующий нужный день недели
                    days_ahead = target_weekday - now.weekday()
                    if days_ahead <= 0:  # Если день уже прошел на этой неделе
                        days_ahead += 7
                    
                    next_weekly = now + timedelta(days=days_ahead)
                    next_weekly = next_weekly.replace(
                        hour=next_run_time.hour, 
                        minute=next_run_time.minute, 
                        second=0, 
                        microsecond=0
                    )
                    # next_weekly уже timezone-aware, так как now имеет timezone
                    # Проверка tzinfo не нужна
                    
                    seconds_until = (next_weekly - now).total_seconds()
                    
                    # Планируем следующее событие
                    context.application.job_queue.run_once(
                        self._send_weekly_event_notification,
                        seconds_until,
                        data={
                            'chat_id': chat_id,
                            'event_name': event_name,
                            'event_type': event_type,
                            'event_text': event_text,
                            'next_run_time': next_run_time,
                            'target_weekday': target_weekday
                        },
                        name=f"weekly_event_{chat_id}_{event_name}"
                    )
                    logger.info(f"✅ Следующее еженедельное событие '{event_name}' настроено через {seconds_until:.0f} секунд")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о еженедельном событии '{event_name}': {e}")