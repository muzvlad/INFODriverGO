"""Основной класс планировщика уведомлений"""
import logging
from datetime import datetime, timedelta
import pytz
import asyncio
from .events_data.three_days_reminder import ThreeDaysReminderMixin

logger = logging.getLogger(__name__)


class JobScheduler(ThreeDaysReminderMixin):
    """Класс для управления планировщиком уведомлений"""
    
    def __init__(self, timezone: pytz.BaseTzInfo, settings_manager=None):
        self.timezone = timezone
        self.group_jobs = {}  # Для основных уведомлений (дни рождения)
        self.event_jobs = {}  # Для событий (отдельное хранилище)
        self._settings_manager = settings_manager
        self._monitor_task = None  # Задача мониторинга
        self.last_notification_times = {}  # Отслеживание времени последних уведомлений
        
    async def start_monitoring(self, job_queue, interval: int = 30):
        """Запускает мониторинг JobQueue"""
        try:
            from .job_monitor import JobMonitorMixin
            monitor = JobMonitorMixin()
            self._monitor_task = asyncio.create_task(
                monitor.monitor_active_jobs(job_queue, interval)
            )
            logger.info(f"✅ Мониторинг JobQueue запущен (интервал: {interval} сек)")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске мониторинга JobQueue: {e}")
            
    async def stop_monitoring(self):
        """Останавливает мониторинг JobQueue"""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("🛑 Мониторинг JobQueue остановлен")
    
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
    
    def setup_group_job(self, chat_id: str, settings_manager, job_queue=None):
        """Настраивает задание для уведомлений в группе"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            notification_time = settings_manager.get_notification_time(chat_id_str)
            
            if not job_queue:
                logger.warning(f"❌ JobQueue недоступен для группы {chat_id_str}")
                return
            
            logger.info(f"🔧 Настройка уведомлений для группы {chat_id_str}")
            logger.info(f"⏰ Время уведомлений: {notification_time.strftime('%H:%M')}")
            
            # Проверяем, включены ли уведомления
            if not settings_manager.is_notifications_enabled(chat_id_str):
                logger.info(f"🔕 Уведомления выключены для группы {chat_id_str}")
                return
            
            # Проверяем состояние JobQueue
            try:
                job_queue_status = "активен" if job_queue.scheduler.running else "не активен"
                logger.info(f"📊 Состояние JobQueue: {job_queue_status}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить состояние JobQueue: {e}")
            
            # Удаляем старое задание если есть
            if chat_id_str in self.group_jobs:
                try:
                    logger.info(f"🗑️ Удаление старого задания для группы {chat_id_str}")
                    self.group_jobs[chat_id_str].schedule_removal()
                    del self.group_jobs[chat_id_str]
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при удалении старого задания для {chat_id_str}: {e}")
            
            # Дополнительно удаляем все задания этой группы из job_queue
            try:
                jobs = job_queue.jobs()
                for job in jobs:
                    if (hasattr(job, 'name') and 
                        (f"group_notification_today_{chat_id_str}" in job.name or
                         f"group_daily_notification_{chat_id_str}" in job.name or
                         f"group_daily_start_{chat_id_str}" in job.name)):
                        job.schedule_removal()
                        logger.info(f"🗑️ Удалено задание из очереди: {job.name}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при очистке job_queue для {chat_id_str}: {e}")
            
            # Создаем ежедневное задание с возможностью сегодняшней отправки
            logger.info(f"➕ Настройка уведомлений для группы {chat_id_str}")
            logger.info(f"⏰ Время уведомлений: {notification_time.strftime('%H:%M')}")
            
            # Проверяем текущее время
            now = datetime.now(self.timezone)
            logger.info(f"🕐 Текущее время: {now.strftime('%H:%M:%S')}")
            
            # Создаем время уведомлений сегодня
            today_notification_naive = datetime.combine(now.date(), notification_time)
            today_notification = self.timezone.localize(today_notification_naive)
            
            # Проверяем, нужно ли отправить поздравление сегодня
            if today_notification > now:
                # Время еще не прошло сегодня - отправляем сегодня
                seconds_until_today = (today_notification - now).total_seconds()
                logger.info(f"✅ Время еще не прошло сегодня, отправим поздравление через {seconds_until_today:.0f} секунд")
                
                # Создаем одноразовое задание для сегодняшней отправки
                job = job_queue.run_once(
                    self.send_group_notification_then_schedule_daily,
                    seconds_until_today,
                    data={'chat_id': chat_id, 'daily_time': notification_time},
                    name=f"group_notification_today_{chat_id_str}"
                )
                self.group_jobs[chat_id_str] = job
                logger.info(f"✅ Настроено одноразовое уведомление на сегодня (через {seconds_until_today:.0f} секунд)")
            else:
                # Время уже прошло сегодня - настраиваем только ежедневное
                logger.info(f"⏭️ Время уже прошло сегодня, настраиваем только ежедневное задание")
                self._setup_daily_job(chat_id, notification_time, job_queue)
            
            # Проверяем, что задание действительно создано
            try:
                jobs = job_queue.jobs()
                job_names = [j.name for j in jobs]
                logger.info(f"📋 Все активные задания: {job_names}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить список заданий: {e}")
            
            # Настраиваем напоминания за 3 дня для личных сообщений
            if self._is_private_chat(chat_id_str):
                try:
                    self.setup_three_days_reminders(chat_id_str, settings_manager, job_queue, self.timezone)
                except Exception as e:
                    logger.error(f"❌ Ошибка при настройке напоминаний за 3 дня: {e}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке уведомлений для группы {chat_id}: {e}")
    
    def update_group_job_time(self, chat_id: str, settings_manager, application=None):
        """Обновляет время уведомлений для группы (только основные уведомления)"""
        chat_id_str = str(chat_id)
        
        # Получаем новое время из настроек
        notification_time = settings_manager.get_notification_time(chat_id_str)
        
        if not application or not application.job_queue:
            return
        
        job_queue = application.job_queue
        
        # Удаляем только основные задания (не трогаем события)
        if chat_id_str in self.group_jobs:
            try:
                logger.info(f"🔄 Обновляем основные уведомления для группы {chat_id_str}")
                self.group_jobs[chat_id_str].schedule_removal()
                del self.group_jobs[chat_id_str]
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при удалении старого задания для {chat_id_str}: {e}")
        
        # Дополнительно удаляем все задания этой группы из job_queue
        try:
            jobs = job_queue.jobs()
            for job in jobs:
                if (hasattr(job, 'name') and 
                    (f"group_notification_today_{chat_id_str}" in job.name or
                     f"group_daily_notification_{chat_id_str}" in job.name or
                     f"group_daily_start_{chat_id_str}" in job.name)):
                    job.schedule_removal()
                    logger.info(f"🗑️ Удалено задание из очереди при обновлении: {job.name}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при очистке job_queue для {chat_id_str}: {e}")
        
        # Проверяем текущее время
        now = datetime.now(self.timezone)
        logger.info(f"🕐 Текущее время: {now.strftime('%H:%M:%S')}")
        logger.info(f"⏰ Новое время уведомлений: {notification_time.strftime('%H:%M')}")
        
        # Создаем время уведомлений сегодня
        today_notification_naive = datetime.combine(now.date(), notification_time)
        today_notification = self.timezone.localize(today_notification_naive)
        
        # Проверяем, нужно ли отправить поздравление сегодня
        if today_notification > now:
            # Новое время еще не наступило сегодня - отправляем сегодня
            seconds_until_today = (today_notification - now).total_seconds()
            logger.info(f"✅ Новое время еще не прошло сегодня, отправим поздравление через {seconds_until_today:.0f} секунд")
            
            # Создаем одноразовое задание для сегодняшней отправки
            job = job_queue.run_once(
                self.send_group_notification_then_schedule_daily,
                seconds_until_today,
                data={'chat_id': chat_id, 'daily_time': notification_time},
                name=f"group_notification_today_{chat_id_str}"
            )
            self.group_jobs[chat_id_str] = job
            logger.info(f"🔄 Создано одноразовое задание на сегодня (через {seconds_until_today:.0f} секунд)")
        else:
            # Новое время уже прошло сегодня - ждем завтра
            logger.info(f"⏭️ Новое время уже прошло сегодня, планируем на завтра")
            # Создаем ежедневное задание с нового времени
            self._setup_daily_job(chat_id, notification_time, job_queue)
            
        logger.info(f"✅ Время основных уведомлений для группы {chat_id_str} обновлено на {notification_time.strftime('%H:%M')}")
        
        # Обновляем напоминания за 3 дня для личных сообщений
        if self._is_private_chat(chat_id_str):
            try:
                # Удаляем старые напоминания
                jobs_to_remove = []
                try:
                    all_jobs = job_queue.jobs()
                    for job in all_jobs:
                        if (hasattr(job, 'name') and 
                            ('birthday_reminder' in job.name or 'wedding_reminder' in job.name) and
                            chat_id_str in job.name):
                            jobs_to_remove.append(job)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при поиске старых напоминаний: {e}")
                
                # Удаляем найденные задания
                for job in jobs_to_remove:
                    try:
                        job.schedule_removal()
                        logger.info(f"🗑️ Удалено старое напоминание: {job.name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при удалении напоминания {job.name}: {e}")
                
                # Настраиваем новые напоминания
                self.setup_three_days_reminders(chat_id_str, settings_manager, job_queue, self.timezone)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обновлении напоминаний за 3 дня: {e}")
    
    def update_event_jobs(self, chat_id: str, settings_manager, application=None):
        """Обновляет задания событий для группы (не влияет на основные уведомления)"""
        chat_id_str = str(chat_id)
        
        if not application or not application.job_queue:
            return
        
        job_queue = application.job_queue
        
        # Удаляем старые задания событий
        removed_count = 0
        jobs_to_remove = []
        
        # Собираем задания событий для удаления
        try:
            all_jobs = job_queue.jobs()
            for job in all_jobs:
                if (hasattr(job, 'name') and 
                    'event_' in job.name and 
                    chat_id_str in job.name):
                    jobs_to_remove.append(job)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при поиске заданий событий: {e}")
        
        # Удаляем найденные задания
        for job in jobs_to_remove:
            try:
                job.schedule_removal()
                removed_count += 1
                logger.info(f"🗑️ Удалено задание события: {job.name}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при удалении задания {job.name}: {e}")
        
        logger.info(f"🔄 Удалено {removed_count} заданий событий для группы {chat_id_str}")
        
        # Настраиваем новые задания событий
        try:
            self.setup_event_jobs(chat_id_str, settings_manager, job_queue, self.timezone, getattr(self, '_bot_ref', None))
            logger.info(f"✅ Задания событий для группы {chat_id_str} обновлены")
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке событий для группы {chat_id_str}: {e}")
    
    async def send_group_notification_then_schedule_daily(self, context):
        """Отправляет уведомление сегодня и настраивает ежедневное планирование"""
        chat_id = context.job.data.get('chat_id')
        daily_time = context.job.data.get('daily_time')
        
        if not chat_id or not daily_time:
            logger.error("❌ Не хватает данных для отправки уведомления")
            return
        
        chat_id_str = str(chat_id)
        logger.info(f"🔔 Отправляем поздравление сегодня для группы {chat_id_str}")
        
        # Отправляем сегодняшнее уведомление
        await self.send_group_notification(context)
        
        # Проверяем текущее время перед настройкой ежедневного задания
        now = datetime.now(self.timezone)
        today_scheduled_time = self.timezone.localize(
            datetime.combine(now.date(), daily_time)
        )
        
        # Настраиваем ежедневное задание только если время еще не прошло сегодня
        if context.application and context.application.job_queue:
            if today_scheduled_time > now:
                # Время еще не прошло сегодня - настраиваем на сегодня
                self._setup_daily_job_for_today(chat_id, daily_time, context.application.job_queue, now)
                logger.info(f"✅ Ежедневное планирование настроено на сегодня {daily_time.strftime('%H:%M')}")
            else:
                # Время уже прошло сегодня - настраиваем на завтра
                self._setup_daily_job(chat_id, daily_time, context.application.job_queue)
                logger.info(f"✅ Ежедневное планирование настроено на завтра {daily_time.strftime('%H:%M')}")
    
    def _setup_daily_job(self, chat_id: str, notification_time, job_queue):
        """Настраивает ежедневное задание с указанным временем (на завтра и далее)"""
        chat_id_str = str(chat_id)
        
        # Создаем timezone-aware время для ежедневного задания
        now = datetime.now(self.timezone)
        scheduled_time = self.timezone.localize(
            datetime.combine(now.date(), notification_time)
        )
        
        # Переносим на завтра (гарантируем, что не сработает сегодня)
        scheduled_time = scheduled_time + timedelta(days=1)
        
        logger.info(f"🕒 Планируем ежедневное уведомление с завтра на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (часовой пояс: {self.timezone.zone})")
        
        # Создаем ежедневное задание
        job = job_queue.run_daily(
            self.send_group_notification,
            time=notification_time,
            days=tuple(range(7)),  # каждый день
            data={'chat_id': chat_id},
            name=f"group_daily_notification_{chat_id_str}"
        )
        
        self.group_jobs[chat_id_str] = job
        logger.info(f"📅 Настроено ежедневное уведомление для группы {chat_id_str} на {notification_time.strftime('%H:%M')} ({self.timezone.zone})")
    
    def _setup_daily_job_for_today(self, chat_id: str, notification_time, job_queue, now):
        """Настраивает ежедневное задание на сегодня (если время еще не прошло)"""
        chat_id_str = str(chat_id)
        
        # Создаем время на сегодня
        scheduled_time = self.timezone.localize(
            datetime.combine(now.date(), notification_time)
        )
        
        seconds_until = (scheduled_time - now).total_seconds()
        
        logger.info(f"🕒 Планируем ежедневное уведомление на сегодня через {seconds_until:.0f} секунд")
        
        # Создаем одноразовое задание на сегодня
        job = job_queue.run_once(
            self._convert_to_daily_after_first_run,
            seconds_until,
            data={
                'chat_id': chat_id,
                'daily_time': notification_time
            },
            name=f"group_daily_start_{chat_id_str}"
        )
        
        self.group_jobs[chat_id_str] = job
        logger.info(f"📅 Настроено стартовое уведомление для группы {chat_id_str} на сегодня {notification_time.strftime('%H:%M')}")
    
    async def _convert_to_daily_after_first_run(self, context):
        """Конвертирует одноразовое задание в ежедневное после первого запуска"""
        chat_id = context.job.data.get('chat_id')
        daily_time = context.job.data.get('daily_time')
        
        if not chat_id or not daily_time:
            logger.error("❌ Не хватает данных для конвертации в ежедневное задание")
            return
        
        chat_id_str = str(chat_id)
        logger.info(f"🔄 Конвертируем одноразовое задание в ежедневное для группы {chat_id_str}")
        
        # Отправляем уведомление
        await self.send_group_notification(context)
        
        # Настраиваем полноценное ежедневное задание на завтра
        if context.application and context.application.job_queue:
            self._setup_daily_job(chat_id, daily_time, context.application.job_queue)
            logger.info(f"✅ Переключено на полноценное ежедневное планирование на {daily_time.strftime('%H:%M')}")
    
    async def send_group_notification(self, context):
        """Отправляет уведомление для конкретной группы"""
        try:
            # Получаем данные из контекста

            
            chat_id = context.job.data.get('chat_id') if hasattr(context.job, 'data') else None
            if not chat_id:
                logger.error("❌ Не указан chat_id для уведомления")
                logger.error(f"❌ Доступные атрибуты context.job: {dir(context.job) if hasattr(context, 'job') else 'Нет job'}")
                return
            
            logger.info(f"🔔 Попытка отправить уведомление для группы {chat_id}")
            
            # Проверяем, не было ли сегодня уже отправлено уведомление (защита от дубликатов)
            chat_id_str = str(chat_id)
            now = datetime.now(self.timezone)
            today_date = now.date()
            
            # Проверяем дату последнего уведомления для этой группы
            if chat_id_str in self.last_notification_times:
                last_date = self.last_notification_times[chat_id_str].date()
                
                # Если уже отправляли сегодня - блокируем
                if last_date == today_date:
                    logger.warning(f"⚠️ Блокировка дублирующего уведомления для группы {chat_id_str}. Уже отправлено сегодня")
                    return
                else:
                    logger.info(f"✅ Новый день - можно отправить уведомление")
            
            # Запоминаем время отправки текущего уведомления
            self.last_notification_times[chat_id_str] = now
            logger.info(f"🕒 Время последнего уведомления для {chat_id_str} установлено на {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Получаем бота из контекста через универсальный метод
            bot = self._get_main_bot(context)
            
            if not bot:
                logger.error("❌ Основной бот не найден в контексте")
                return
            
            # Получаем реального Telegram бота
            telegram_bot = None
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'bot')):
                telegram_bot = context.application.bot
            elif hasattr(context, 'bot'):
                telegram_bot = context.bot
            
            if not telegram_bot:
                logger.error("❌ Не удалось получить Telegram бота для поздравлений")
                return
            
            # Создаем фейковый контекст с реальным Telegram ботом
            class FakeContext:
                def __init__(self, telegram_bot_instance, job_data):
                    self.bot = telegram_bot_instance
                    self.job = type('FakeJob', (), {'data': job_data})()
                    self.application = type('FakeApplication', (), {'bot': telegram_bot_instance})()
            
            fake_context = FakeContext(telegram_bot, context.job.data)
            
            # Вызываем метод отправки уведомления из основного бота
            await bot.send_group_notification(fake_context)
            logger.info(f"✅ Уведомление успешно отправлено для группы {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления в группу {chat_id}: {e}")
    
    def _get_main_bot(self, context):
        """Универсальный метод для получения основного бота из контекста"""
        try:
            # Приоритет 1: Через application.main_bot
            if (hasattr(context, 'application') and 
                hasattr(context.application, 'main_bot')):
                return context.application.main_bot
            
            # Приоритет 2: Через self._settings_manager_ref если есть
            if (hasattr(self, '_settings_manager_ref') and 
                hasattr(self._settings_manager_ref, 'bot')):
                return self._settings_manager_ref.bot
            
            # Приоритет 3: Через глобальный доступ (если сохранен)
            import sys
            if hasattr(sys.modules.get('backend.main_bot', None), 'MainBot'):
                # Попытка получить через singleton
                pass
            
            logger.warning("⚠️ Основной бот не найден в контексте, пытаюсь получить через settings_manager")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении основного бота: {e}")
            return None