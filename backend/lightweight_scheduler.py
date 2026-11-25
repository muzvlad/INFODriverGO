"""Упрощенный планировщик задач для Raspberry Pi"""
import logging
from datetime import datetime, timedelta
import pytz
import asyncio

logger = logging.getLogger(__name__)


class LightweightJobScheduler:
    """Облегченный класс для управления планировщиком уведомлений"""
    
    def __init__(self, timezone: pytz.BaseTzInfo):
        self.timezone = timezone
        self.active_jobs = {}  # Только активные задания
        self._cleanup_task = None
        
    async def start_cleanup_monitor(self, job_queue, interval: int = 60):
        """Запускает периодическую очистку завершенных заданий"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    self._cleanup_completed_jobs()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Ошибка в cleanup loop: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"✅ Cleanup monitor запущен (интервал: {interval} сек)")
    
    async def stop_cleanup_monitor(self):
        """Останавливает cleanup monitor"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("🛑 Cleanup monitor остановлен")
    
    def _cleanup_completed_jobs(self):
        """Очищает завершенные задания из внутреннего хранилища"""
        completed_jobs = []
        for job_name, job_ref in self.active_jobs.items():
            if hasattr(job_ref, 'removed') and job_ref.removed:
                completed_jobs.append(job_name)
        
        for job_name in completed_jobs:
            self.active_jobs.pop(job_name, None)
        
        if completed_jobs:
            logger.debug(f"Очищено {len(completed_jobs)} завершенных заданий")
    
    def setup_group_job(self, chat_id: str, settings_manager, job_queue=None):
        """Настраивает задание для уведомлений в группе (упрощенная версия)"""
        try:
            chat_id_str = str(chat_id)
            
            if not job_queue:
                logger.warning(f"❌ JobQueue недоступен для группы {chat_id_str}")
                return
            
            # Получаем настройки группы
            notification_time = settings_manager.get_notification_time(chat_id_str)
            
            # Проверяем, включены ли уведомления
            if not settings_manager.is_notifications_enabled(chat_id_str):
                logger.info(f"🔕 Уведомления выключены для группы {chat_id_str}")
                return
            
            # Удаляем старое задание если есть
            self._remove_existing_job(chat_id_str, job_queue)
            
            # Создаем новое задание
            self._create_notification_job(chat_id_str, notification_time, job_queue)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке уведомлений для группы {chat_id}: {e}")
    
    def _remove_existing_job(self, chat_id_str: str, job_queue):
        """Удаляет существующие задания для группы"""
        # Удаляем из нашего хранилища
        if chat_id_str in self.active_jobs:
            try:
                self.active_jobs[chat_id_str].schedule_removal()
                del self.active_jobs[chat_id_str]
                logger.debug(f"Удалено старое задание для {chat_id_str}")
            except Exception as e:
                logger.warning(f"Ошибка при удалении задания для {chat_id_str}: {e}")
        
        # Удаляем из job_queue напрямую
        try:
            jobs = job_queue.jobs()
            for job in jobs:
                if (hasattr(job, 'name') and 
                    (f"group_notification_today_{chat_id_str}" in job.name or
                     f"group_daily_notification_{chat_id_str}" in job.name)):
                    job.schedule_removal()
                    logger.debug(f"Удалено задание из очереди: {job.name}")
        except Exception as e:
            logger.warning(f"Ошибка при очистке job_queue: {e}")
    
    def _create_notification_job(self, chat_id_str: str, notification_time, job_queue):
        """Создает задание уведомления"""
        now = datetime.now(self.timezone)
        today_notification_naive = datetime.combine(now.date(), notification_time)
        today_notification = self.timezone.localize(today_notification_naive)
        
        if today_notification > now:
            # Время еще не прошло сегодня - отправляем сегодня
            seconds_until_today = (today_notification - now).total_seconds()
            logger.info(f"✅ Настройка одноразового уведомления через {seconds_until_today:.0f} сек")
            
            job = job_queue.run_once(
                self._send_notification_callback,
                seconds_until_today,
                data={'chat_id': chat_id_str},
                name=f"group_notification_today_{chat_id_str}"
            )
            self.active_jobs[chat_id_str] = job
        else:
            # Время уже прошло - настраиваем ежедневное
            logger.info(f"⏭️ Настройка ежедневного уведомления на {notification_time.strftime('%H:%M')}")
            
            job = job_queue.run_daily(
                self._send_notification_callback,
                time=notification_time,
                days=tuple(range(7)),
                data={'chat_id': chat_id_str},
                name=f"group_daily_notification_{chat_id_str}"
            )
            self.active_jobs[chat_id_str] = job
    
    async def _send_notification_callback(self, context):
        """Callback для отправки уведомлений"""
        try:
            chat_id = context.job.data['chat_id']
            logger.info(f"📤 Отправка уведомления для группы {chat_id}")
            
            # Здесь должна быть логика отправки сообщения
            # Пока просто логируем
            
        except Exception as e:
            logger.error(f"❌ Ошибка в callback уведомления: {e}")
    
    def get_active_jobs_count(self) -> int:
        """Возвращает количество активных заданий"""
        return len(self.active_jobs)
    
    def get_job_stats(self) -> dict:
        """Возвращает статистику по заданиям"""
        return {
            'active_jobs': len(self.active_jobs),
            'job_names': list(self.active_jobs.keys())
        }


# Глобальный экземпляр
lightweight_scheduler = LightweightJobScheduler(pytz.timezone('Europe/Moscow'))