"""Модуль для работы с ежемесячными событиями"""
import logging
from datetime import datetime, timedelta
import pytz
import calendar

logger = logging.getLogger(__name__)


class MonthlyEventsMixin:
    """Миксин для работы с ежемесячными событиями"""
    
    def _setup_monthly_event(self, chat_id: str, event_name: str, time_str: str, job_queue, timezone, event_text: str):
        """Настраивает ежемесячное событие"""
        try:
            logger.info(f"⚙️ Настраиваем ежемесячное событие '{event_name}' в {time_str} для группы {chat_id}")
            
            # Поддерживаем два формата:
            # 1. "ДД_ЧЧ:ММ" (например, "15_20:00")
            # 2. "ДД.ММ.ГГГГ_ЧЧ:ММ" (например, "25.01.2026_20:00") - для одноразовых
            
            if '_' in time_str and '.' not in time_str:
                # Формат "ДД_ЧЧ:ММ" - ежемесячное событие
                day_part, time_part = time_str.split('_', 1)
                day_of_month = int(day_part)
                hour, minute = map(int, time_part.split(':'))
            elif '_' in time_str and '.' in time_str:
                # Формат "ДД.ММ.ГГГГ_ЧЧ:ММ" - одноразовое событие, но обрабатываем как ежемесячное
                date_part, time_part = time_str.split('_', 1)
                day_part, month_part, year_part = date_part.split('.')
                day_of_month = int(day_part)
                hour, minute = map(int, time_part.split(':'))
                # Для ежемесячных событий игнорируем год и месяц, используем только день
                logger.info(f"⚠️ Используется формат одноразового события для ежемесячного. Будет повторяться каждый месяц {day_of_month}-го числа.")
            else:
                logger.error(f"❌ Неверный формат времени для ежемесячного события: {time_str}")
                logger.error("❗ ПРАВИЛЬНЫЙ ФОРМАТ ДЛЯ ЕЖЕМЕСЯЧНЫХ СОБЫТИЙ:")
                logger.error("   /событие ежемесячно ДД_ЧЧ:ММ название")
                logger.error("   Пример: /событие ежемесячно 15_10:00 зарплата")
                logger.error("")
                logger.error("Доступные форматы:")
                logger.error("• Ежемесячные: ДД_ЧЧ:ММ (например: 15_10:00)")
                logger.error("• Одноразовые: ДД.ММ.ГГГГ_ЧЧ:ММ (например: 25.12.2026_12:00)")
                return
            
            # Получаем текущую дату
            now = datetime.now(timezone)
            
            # Создаем дату события в этом месяце
            try:
                this_month_event = timezone.localize(
                    datetime(now.year, now.month, day_of_month, hour, minute)
                )
            except ValueError:
                # Если такой даты нет в этом месяце (например, 31 февраля), используем последний день
                last_day = calendar.monthrange(now.year, now.month)[1]
                this_month_event = timezone.localize(
                    datetime(now.year, now.month, last_day, hour, minute)
                )
                logger.warning(f"⚠️ День {day_of_month} отсутствует в этом месяце, используем последний день {last_day}")
            
            # Если событие в этом месяце еще не прошло - ставим его сегодня
            if this_month_event > now:
                scheduled_time = this_month_event
                logger.info(f"✅ Событие '{event_name}' запланировано на этот месяц: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                # Иначе планируем на следующий месяц
                if now.month == 12:
                    next_year = now.year + 1
                    next_month = 1
                else:
                    next_year = now.year
                    next_month = now.month + 1
                
                try:
                    scheduled_time = timezone.localize(
                        datetime(next_year, next_month, day_of_month, hour, minute)
                    )
                except ValueError:
                    # Если такой даты нет в следующем месяце
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    scheduled_time = timezone.localize(
                        datetime(next_year, next_month, last_day, hour, minute)
                    )
                    logger.warning(f"⚠️ День {day_of_month} отсутствует в следующем месяце, используем последний день {last_day}")
                
                logger.info(f"🕒 Событие '{event_name}' перенесено на следующий месяц: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            seconds_until = (scheduled_time - now).total_seconds()
            
            logger.info(f"🕒 Планируем ежемесячное событие '{event_name}' на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone.zone})")
            
            job = job_queue.run_once(
                self.send_monthly_event_notification,
                seconds_until,
                data={
                    'chat_id': chat_id, 
                    'event_name': event_name, 
                    'event_time': time_str,
                    'event_text': event_text,
                    'day_of_month': day_of_month
                },
                name=f"monthly_event_{chat_id}_{event_name}"
            )
            
            logger.info(f"✅ Настроено ежемесячное событие '{event_name}' через {seconds_until:.0f} секунд ({timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке ежемесячного события '{event_name}': {e}")
    
    async def send_monthly_event_notification(self, context):
        """Отправляет уведомление о ежемесячном событии и настраивает следующее"""
        try:
            chat_id = context.job.data.get('chat_id')
            event_name = context.job.data.get('event_name')
            event_time = context.job.data.get('event_time')
            
            if not chat_id or not event_name or not event_time:
                logger.error("❌ Не хватает данных для отправки уведомления о ежемесячном событии")
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
            logger.info(f"✅ Уведомление о ежемесячном событии '{event_name}' отправлено в группу {chat_id}")
            
            # Настраиваем следующее событие через месяц
            if context.application and context.application.job_queue:
                import pytz
                from config import config
                timezone = pytz.timezone(config.TIMEZONE)
                
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
                
                self._setup_monthly_event(chat_id, event_name, event_time, context.application.job_queue, timezone, event_text)
                logger.info(f"✅ Следующее ежемесячное событие '{event_name}' настроено")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о ежемесячном событии '{event_name}': {e}")