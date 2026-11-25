"""Модуль для работы с уведомлениями свадеб"""
import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger(__name__)


class WeddingSchedulerMixin:
    """Миксин для работы с уведомлениями свадеб"""
    
    def setup_wedding_jobs(self, chat_id: str, settings_manager, job_queue=None):
        """Настраивает задания для свадеб в группе (ежегодные уведомления)"""
        try:
            chat_id_str = str(chat_id)
            
            if not job_queue:
                logger.warning(f"❌ JobQueue недоступен для группы {chat_id_str}")
                return
            
            # Получаем свадьбы для группы
            weddings = settings_manager.get_weddings_for_group(chat_id_str)
            
            if weddings:
                # Настраиваем ежегодные уведомления о свадьбах (отдельно от ежедневной проверки)
                # Ежедневная проверка свадеб уже происходит в основном задании
                for wedding_key, wedding_data in weddings.items():
                    try:
                        name = wedding_data['name']
                        day = int(wedding_data['day'])
                        month = int(wedding_data['month'])
                        
                        # Настраиваем ежегодное уведомление
                        self._setup_annual_wedding(chat_id_str, name, day, month, job_queue)
                    except Exception as e:
                        logger.error(f"❌ Ошибка при настройке ежегодного уведомления о свадьбе {wedding_key}: {e}")
                
                logger.info(f"✅ Настроены ежегодные уведомления о свадьбах для группы {chat_id_str}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке свадеб для группы {chat_id}: {e}")
    
    def _setup_daily_wedding_check(self, chat_id: str, job_queue):
        """Настраивает ежедневную проверку свадеб (аналогично дням рождения)"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем время уведомлений для группы
            notification_time = self._get_group_notification_time(chat_id_str)
            if not notification_time:
                # Используем время по умолчанию 19:25
                notification_time = time(hour=19, minute=25)
            
            logger.info(f"🕒 Планируем ежедневную проверку свадеб для группы {chat_id_str} на {notification_time.strftime('%H:%M')} ({self.timezone.zone})")
            
            # Создаем ежедневное задание
            job = job_queue.run_daily(
                self.check_and_send_wedding_notifications,
                time=notification_time,
                days=tuple(range(7)),  # каждый день
                data={'chat_id': chat_id_str},
                name=f"daily_wedding_check_{chat_id_str}"
            )
            
            logger.info(f"✅ Настроена ежедневная проверка свадеб для группы {chat_id_str} на {notification_time.strftime('%H:%M')} ({self.timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке ежедневной проверки свадеб для группы {chat_id}: {e}")
    
    async def check_and_send_wedding_notifications(self, context):
        """Проверяет и отправляет уведомления о свадьбах"""
        try:
            chat_id = context.job.data.get('chat_id')
            if not chat_id:
                logger.error("❌ Не указан chat_id для проверки свадеб")
                return
            
            # Получаем бота из контекста
            bot = None
            if hasattr(context, 'application') and hasattr(context.application, 'main_bot'):
                bot = context.application.main_bot
            
            if not bot:
                logger.error("❌ BirthdayBot не найден в контексте")
                return
            
            # Получаем свадьбы для группы
            weddings = bot.settings_manager.get_weddings_for_group(chat_id)
            if not weddings:
                return
            
            # Получаем сегодняшнюю дату
            today = datetime.now(self.timezone)
            today_day = today.day
            today_month = today.month
            
            # Проверяем каждую свадьбу
            for wedding_key, wedding_data in weddings.items():
                wedding_day = int(wedding_data['day'])
                wedding_month = int(wedding_data['month'])
                wedding_name = wedding_data['name']
                
                # Если сегодня день свадьбы
                if wedding_day == today_day and wedding_month == today_month:
                    # Отправляем уведомление
                    wedding_context = type('WContext', (), {
                        'job': type('Job', (), {
                            'data': {
                                'chat_id': chat_id,
                                'wedding_name': wedding_name,
                                'wedding_day': wedding_day,
                                'wedding_month': wedding_month
                            }
                        })(),
                        'application': context.application,
                        'bot': context.bot
                    })()
                    
                    await bot.send_wedding_notification(wedding_context)
                    logger.info(f"✅ Отправлено уведомление о свадьбе '{wedding_name}' в группу {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке свадеб для группы {chat_id}: {e}")
    
    def _setup_annual_wedding(self, chat_id: str, name: str, day: int, month: int, job_queue):
        """Настраивает ежегодное уведомление о свадьбе"""
        try:
            # Создаем timezone-aware время для ежегодного уведомления
            now = datetime.now(self.timezone)
            
            # Создаем дату в текущем году
            try:
                wedding_this_year = self.timezone.localize(
                    datetime(now.year, month, day, 9, 0)  # 9:00 утра по умолчанию
                )
            except ValueError:
                # Если дата невалидна (например, 29 февраля в невисокосный год)
                logger.warning(f"⚠️ Невалидная дата свадьбы {day}.{month} для {name}")
                return
            
            # Если дата уже прошла в этом году, переносим на следующий год
            if wedding_this_year < now:
                try:
                    wedding_next_year = self.timezone.localize(
                        datetime(now.year + 1, month, day, 9, 0)
                    )
                    scheduled_time = wedding_next_year
                except ValueError:
                    logger.warning(f"⚠️ Невалидная дата свадьбы {day}.{month} для следующего года для {name}")
                    return
            else:
                scheduled_time = wedding_this_year
            
            # Проверяем текущее время уведомлений группы
            group_notification_time = self._get_group_notification_time(chat_id)
            if group_notification_time:
                # Используем время уведомлений группы вместо 9:00
                scheduled_time = scheduled_time.replace(
                    hour=group_notification_time.hour,
                    minute=group_notification_time.minute
                )
            
            logger.info(f"🕒 Планируем ежегодное уведомление о свадьбе '{name}' на {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({self.timezone.zone})")
            
            # Создаем ежегодное задание
            job = job_queue.run_once(
                self.send_wedding_notification,
                (scheduled_time - now).total_seconds(),
                data={'chat_id': chat_id, 'wedding_name': name, 'wedding_day': day, 'wedding_month': month},
                name=f"annual_wedding_{chat_id}_{name}_{scheduled_time.year}"
            )
            
            logger.info(f"✅ Настроено ежегодное уведомление о свадьбе '{name}' через {(scheduled_time - now).total_seconds():.0f} секунд ({self.timezone.zone})")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке ежегодного уведомления о свадьбе '{name}': {e}")
    
    async def send_wedding_notification(self, context):
        """Отправляет уведомление о годовщине свадьбы"""
        try:
            chat_id = context.job.data.get('chat_id')
            wedding_name = context.job.data.get('wedding_name')
            wedding_day = context.job.data.get('wedding_day')
            wedding_month = context.job.data.get('wedding_month')
            
            if not chat_id or not wedding_name:
                logger.error("❌ Не хватает данных для отправки уведомления о свадьбе")
                return
            
            # Получаем бота из контекста
            bot = None
            if hasattr(context, 'application') and hasattr(context.application, 'main_bot'):
                bot = context.application.main_bot
            
            if not bot:
                logger.error("❌ BirthdayBot не найден в контексте")
                return
            
            # Отправляем уведомление о свадьбе
            await bot.send_wedding_notification(context)
            logger.info(f"✅ Уведомление о свадьбе '{wedding_name}' отправлено в группу {chat_id}")
            
            # Настраиваем следующее уведомление на следующий год
            if context.application and context.application.job_queue:
                # Перепланируем на следующий год
                self._setup_annual_wedding(
                    chat_id, 
                    wedding_name, 
                    wedding_day, 
                    wedding_month, 
                    context.application.job_queue
                )
                logger.info(f"✅ Следующее уведомление о свадьбе '{wedding_name}' запланировано на следующий год")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления о свадьбе '{wedding_name}': {e}")