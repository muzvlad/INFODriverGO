"""Вспомогательные функции для планировщика"""
import logging
from datetime import time

logger = logging.getLogger(__name__)


class SchedulerUtilsMixin:
    """Миксин с вспомогательными функциями для планировщика"""
    
    def clear_existing_jobs(self, job_queue, chat_id: str = None):
        """Очищает существующие задания для указанной группы или все задания"""
        try:
            if not job_queue:
                return
            
            jobs = job_queue.jobs()
            removed_count = 0
            
            for job in jobs:
                # Если указана группа, удаляем только её задания
                if chat_id:
                    if (hasattr(job, 'data') and 
                        isinstance(job.data, dict) and 
                        job.data.get('chat_id') == chat_id):
                        job.schedule_removal()
                        removed_count += 1
                else:
                    # Удаляем все задания
                    job.schedule_removal()
                    removed_count += 1
            
            if chat_id:
                logger.info(f"🧹 Очищено {removed_count} заданий для группы {chat_id}")
            else:
                logger.info(f"🧹 Очищено {removed_count} заданий из очереди")
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при очистке заданий: {e}")
    
    def _get_group_notification_time(self, chat_id: str):
        """Получает время уведомлений для группы"""
        try:
            # Получаем время уведомлений из settings_manager
            if hasattr(self, '_settings_manager'):
                return self._settings_manager.get_notification_time(chat_id)
            
            # Если settings_manager не доступен, возвращаем None
            # Будет использовано значение по умолчанию
            return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения времени уведомлений для группы {chat_id}: {e}")
            return None