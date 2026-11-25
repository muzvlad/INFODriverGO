"""Модуль для работы с одноразовыми событиями"""
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)


class OneTimeEventsMixin:
    """Миксин для работы с одноразовыми событиями"""
    
    def _setup_one_time_event(self, chat_id: str, event_name: str, time_str: str, job_queue, timezone, event_text: str):
        """Настраивает одноразовое событие"""
        try:
            logger.info(f"⚙️ Настраиваем одноразовое событие '{event_name}' в {time_str} для группы {chat_id}")
            
            # Парсим дату и время из time_str (формат: "ДД.ММ.ГГГГ_ЧЧ:ММ")
            date_part, time_part = time_str.split('_', 1)
            day, month, year = map(int, date_part.split('.'))
            hour, minute = map(int, time_part.split(':'))
            
            # Создаем timezone-aware datetime
            scheduled_time = timezone.localize(
                datetime(year, month, day, hour, minute)
            )
            
            now = datetime.now(timezone)
            
            # Проверяем, что время еще не прошло
            if scheduled_time <= now:
                logger.error(f"❌ Время события '{event_name}' уже прошло: {scheduled_time}")
                return
            
            seconds_until = (scheduled_time - now).total_seconds()
            
            logger.info(f"🕒 Планируем одноразовое событие '{event_name}' на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone.zone})")
            
            job = job_queue.run_once(
                self.send_event_notification,
                seconds_until,
                data={
                    'chat_id': chat_id, 
                    'event_name': event_name, 
                    'event_type': 'одноразово',
                    'event_text': event_text
                },
                name=f"onetime_event_{chat_id}_{event_name}"
            )
            
            logger.info(f"✅ Настроено одноразовое событие '{event_name}' через {seconds_until:.0f} секунд ({timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке одноразового события '{event_name}': {e}")