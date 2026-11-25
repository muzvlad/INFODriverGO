"""Система планирования событий с поддержкой различных типов повторений"""
import logging
from datetime import datetime, timedelta

from .events_data import (
    OneTimeEventsMixin,
    DailyEventsMixin, 
    WeeklyEventsMixin,
    MonthlyEventsMixin
)

logger = logging.getLogger(__name__)


class EventSchedulerMixin(
    OneTimeEventsMixin,
    DailyEventsMixin, 
    WeeklyEventsMixin,
    MonthlyEventsMixin
):
    """Миксин для работы с уведомлениями событий"""
    
    def __init__(self):
        self._settings_manager_ref = None
        self._bot_ref = None
    
    def _remove_existing_event_jobs(self, chat_id: str, job_queue):
        """Удаляет существующие задания событий для указанной группы"""
        try:
            if not job_queue or not hasattr(job_queue, 'jobs'):
                return
            
            jobs = job_queue.jobs()
            removed_count = 0
            
            for job in jobs:
                # Проверяем, является ли задание событием для этой группы
                if (hasattr(job, 'name') and 
                    'event_' in job.name and 
                    chat_id in job.name):
                    try:
                        job.schedule_removal()
                        removed_count += 1
                        logger.info(f"🗑️ Удалено старое задание события: {job.name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при удалении задания {job.name}: {e}")
            
            if removed_count > 0:
                logger.info(f"✅ Удалено {removed_count} старых заданий событий для группы {chat_id}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении существующих заданий событий: {e}")
    
    def setup_event_jobs(self, chat_id: str, settings_manager, job_queue=None, timezone=None, bot=None):
        """Настраивает задания для всех типов событий в группе"""
        try:
            chat_id_str = str(chat_id)
            
            # Сохраняем ссылки для последующего использования
            self._settings_manager_ref = settings_manager
            if bot:
                self._bot_ref = bot
            
            if not job_queue:
                logger.warning(f"❌ JobQueue недоступен для группы {chat_id_str}")
                return
            
            # Получаем часовой пояс
            if timezone is None:
                import pytz
                from config import config
                timezone = pytz.timezone(config.TIMEZONE)
            
            # Удаляем существующие задания событий для этой группы
            self._remove_existing_event_jobs(chat_id_str, job_queue)
            
            # Получаем события для группы
            events = settings_manager.get_events_for_group(chat_id_str)
            logger.info(f"Найдено {len(events)} событий для группы {chat_id_str}: {list(events.keys())}")
            
            for event_key, event_data in events.items():
                event_type = event_data.get('type', '').lower()
                event_time = event_data.get('time', '')
                event_name = event_data.get('name', '')
                event_text = event_data.get('text', f"{event_name} начинается!")
                
                logger.info(f"Обрабатываем событие: {event_name} (тип: {event_type}, время: {event_time})")
                logger.info(f"📝 Текст события: {event_text}")
                
                if event_type == 'одноразово':
                    self._setup_one_time_event(chat_id_str, event_name, event_time, job_queue, timezone, event_text)
                elif event_type == 'ежедневно':
                    self._setup_daily_event(chat_id_str, event_name, event_time, job_queue, timezone, event_text)
                elif event_type == 'еженедельно':
                    self._setup_weekly_event(chat_id_str, event_name, event_time, job_queue, timezone, event_text)
                elif event_type == 'двухнедельно':
                    self._setup_biweekly_event(chat_id_str, event_name, event_time, job_queue, timezone, event_text)
                elif event_type == 'ежемесячно':
                    self._setup_monthly_event(chat_id_str, event_name, event_time, job_queue, timezone, event_text)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке событий для группы {chat_id}: {e}")
    
    async def send_event_notification(self, context):
        """Отправляет уведомление о событии через основной бот"""
        try:
            if not self._bot_ref:
                logger.error("❌ Бот не доступен для отправки уведомления о событии")
                return
            
            # Вызываем метод из основного бота
            await self._bot_ref.send_event_notification(context)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о событии: {e}")
    
