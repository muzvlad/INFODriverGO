"""Главный модуль планировщика - объединяет все компоненты"""
from .job_scheduler import JobScheduler
from .wedding_scheduler import WeddingSchedulerMixin
from .event_scheduler import EventSchedulerMixin
from .scheduler_utils import SchedulerUtilsMixin

# Объединяем все миксины в один класс
class UnifiedJobScheduler(JobScheduler, WeddingSchedulerMixin, EventSchedulerMixin, SchedulerUtilsMixin):
    """Унифицированный планировщик, объединяющий все функциональности"""
    pass

# Экспортируем основной класс
__all__ = ['UnifiedJobScheduler', 'JobScheduler']