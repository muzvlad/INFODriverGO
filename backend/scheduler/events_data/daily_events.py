"""Модуль для работы с ежедневными событиями"""
import logging
from datetime import datetime, timedelta, time
import pytz

logger = logging.getLogger(__name__)


class DailyEventsMixin:
    """Миксин для работы с ежедневными событиями"""
    
    def _setup_daily_event(self, chat_id: str, event_name: str, time_str: str, job_queue, timezone, event_text: str):
        """Настраивает ежедневное событие"""
        try:
            logger.info(f"⚙️ Настраиваем ежедневное событие '{event_name}' в {time_str} для группы {chat_id}")
            
            # Парсим время из time_str (формат: "ЧЧ:ММ")
            hour, minute = map(int, time_str.split(':'))
            
            # Получаем текущую дату и время в часовом поясе бота
            now = datetime.now(timezone)
            event_time = time(hour, minute)
            
            # Создаем дату события на сегодня
            scheduled_time = timezone.localize(
                datetime.combine(now.date(), event_time)
            )
            
            # Если время уже прошло сегодня, переносим на завтра
            if scheduled_time <= now:
                scheduled_time = scheduled_time + timedelta(days=1)
                logger.info(f"⚠️ Время {time_str} уже прошло сегодня, переносим событие на завтра")
            
            logger.info(f"🕒 Планируем ежедневное событие '{event_name}' на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone.zone})")
            
            # Используем run_once с автоматическим перепланированием для постоянного ежедневного повторения
            seconds_until = (scheduled_time - now).total_seconds()
            
            job = job_queue.run_once(
                self.send_event_notification,
                seconds_until,
                data={
                    'chat_id': chat_id, 
                    'event_name': event_name, 
                    'event_type': 'ежедневно',
                    'event_text': event_text,
                    'next_run_time': time(hour, minute)  # Сохраняем время для следующего запуска
                },
                name=f"daily_event_{chat_id}_{event_name}"
            )
            
            logger.info(f"✅ Настроено ежедневное событие '{event_name}' на {time_str} ({timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке ежедневного события '{event_name}': {e}")
    
    async def send_event_notification(self, context):
        """Отправляет уведомление о ежедневном событии и настраивает следующее"""
        try:
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            event_type = context.job.data.get('event_type')
            event_text = context.job.data.get('event_text')
            next_run_time = context.job.data.get('next_run_time')
            
            if not chat_id or not event_name or not next_run_time:
                logger.error("❌ Не хватает данных для отправки уведомления о ежедневном событии")
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
            logger.info(f"✅ Уведомление о ежедневном событии '{event_name}' отправлено в группу {chat_id}")
            
            # Настраиваем следующее событие через день
            if context.application and context.application.job_queue:
                import pytz
                from config import config
                timezone = pytz.timezone(config.TIMEZONE)
                now = datetime.now(timezone)
                
                # Планируем следующее событие на завтра в то же время
                tomorrow = now + timedelta(days=1)
                # Создаем naive datetime и затем локализуем его
                naive_datetime = datetime.combine(tomorrow.date(), next_run_time)
                next_scheduled = timezone.localize(naive_datetime)
                
                seconds_until = (next_scheduled - now).total_seconds()
                
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
                    self.send_event_notification,
                    seconds_until,
                    data={
                        'chat_id': chat_id,
                        'event_name': event_name,
                        'event_type': event_type,
                        'event_text': event_text,
                        'next_run_time': next_run_time
                    },
                    name=f"daily_event_{chat_id}_{event_name}"
                )
                logger.info(f"✅ Следующее ежедневное событие '{event_name}' настроено через {seconds_until:.0f} секунд")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о ежедневном событии '{event_name}': {e}")