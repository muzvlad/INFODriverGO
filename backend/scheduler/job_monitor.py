"""Модуль для мониторинга и отладки JobQueue"""
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class JobMonitorMixin:
    """Миксин для мониторинга заданий в JobQueue"""
    
    async def monitor_active_jobs(self, job_queue, interval: int = 30):
        """
        Мониторит задания в JobQueue
        
        Args:
            job_queue: JobQueue для мониторинга
            interval: Интервал проверки в секундах
        """
        try:
            last_job_count = 0
            monitored_groups = set()  # Отслеживаем группы, по которым уже выводили информацию
            
            while True:
                try:
                    if job_queue and hasattr(job_queue, 'jobs'):
                        jobs = job_queue.jobs()
                        current_job_count = len(jobs)
                        
                        # Выводим информацию только если количество заданий изменилось
                        if current_job_count != last_job_count:
                            logger.info(f"📊 СОСТОЯНИЕ JOBQUEUE ИЗМЕНИЛОСЬ:")
                            logger.info(f"   Всего заданий: {current_job_count}")
                            
                            # Группируем задания по группам
                            group_jobs = {}
                            for job in jobs:
                                if hasattr(job, 'name'):
                                    # Извлекаем chat_id из имени задания
                                    job_name = job.name
                                    chat_id = None
                                    
                                    # Пытаемся найти chat_id в имени задания
                                    import re
                                    chat_id_match = re.search(r'(-?\d+)', job_name)
                                    if chat_id_match:
                                        chat_id = chat_id_match.group(1)
                                        if chat_id not in group_jobs:
                                            group_jobs[chat_id] = []
                                        group_jobs[chat_id].append(job)
                            
                            # Выводим информацию только по группам, где произошли изменения
                            for chat_id, jobs_list in group_jobs.items():
                                if chat_id not in monitored_groups:
                                    logger.info(f"   📋 Группа {chat_id}:")
                                    for i, job in enumerate(jobs_list):
                                        job_type = "📅 Событие" if 'event_' in job.name else \
                                                   "💍 Свадьба" if 'wedding' in job.name.lower() else \
                                                   "📅 Ежедневное" if 'daily' in job.name.lower() else \
                                                   "ℹ️ Обычное"
                                        logger.info(f"      {i+1}. {job.name} ({job_type})")
                                    monitored_groups.add(chat_id)
                            
                            last_job_count = current_job_count
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка при мониторинге JobQueue: {e}")
                    logger.error(f"   Тип ошибки: {type(e).__name__}")
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info("🛑 Мониторинг JobQueue остановлен")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в мониторинге JobQueue: {e}")

    def debug_job_execution(self, context):
        """
        Отладочная функция для проверки выполнения заданий
        
        Args:
            context: Контекст выполнения задания
        """
        try:
            logger.info("ОТЛАДКА ВЫПОЛНЕНИЯ ЗАДАНИЯ:")
            logger.info(f"   Job name: {getattr(context.job, 'name', 'Неизвестно')}")
            logger.info(f"   Job data: {getattr(context.job, 'data', 'Нет данных')}")
            logger.info(f"   Context type: {type(context)}")
            logger.info(f"   Context attributes: {dir(context)}")
            
            if hasattr(context, 'application'):
                logger.info(f"   Application available: ✅")
                if hasattr(context.application, 'job_queue'):
                    logger.info(f"   JobQueue available: ✅")
                else:
                    logger.info(f"   JobQueue available: ❌")
            else:
                logger.info(f"   Application available: ❌")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в отладке задания: {e}")