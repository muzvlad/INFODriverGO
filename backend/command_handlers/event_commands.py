import logging
import re
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class EventCommands(BaseCommandHandler):
    """Класс для обработки команд событий"""
    
    async def add_event_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда добавления события"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=3)
        
        if len(parts) < 4:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
                "Используйте: `/событие ТИП ЧАСЫ_МИНУТЫ НАЗВАНИЕ`\n"
                "Например: `/событие ежедневно 21:00 Руины`\n"
                "Например: `/событие еженедельно понедельник_21:00 Руины`\n"
                "Например: `/событие ежемесячно 01_21:00 Руины`\n"
                "Допустимые типы: ежедневно, еженедельно, двухнедельно, ежемесячно, одноразово"
            )
            return
        
        # Извлекаем параметры
        event_type = parts[1].strip().lower()
        time_str = parts[2].strip()
        event_name = parts[3].strip()
        
        # Проверяем допустимые типы событий
        valid_types = ['ежедневно', 'еженедельно', 'двухнедельно', 'ежемесячно', 'одноразово']
        if event_type not in valid_types:
            await update.message.reply_text(
                "❌ Неверный тип события!\n"
                "Допустимые типы: ежедневно, еженедельно, двухнедельно, ежемесячно, одноразово"
            )
            return
        
        # Проверяем формат времени
        if event_type == 'одноразово':
            # Для одноразовых событий формат: ДД.ММ.ГГГГ_ЧЧ:ММ
            time_pattern = r'^(\d{1,2})\.(\d{1,2})\.(\d{4})_(\d{1,2}):(\d{2})$'
            match = re.match(time_pattern, time_str)
            if not match:
                await update.message.reply_text(
                    "❌ Неверный формат времени для одноразового события!\n"
                    "Используйте формат: ДД.ММ.ГГГГ_ЧЧ:ММ\n"
                    "Например: `15.03.2024_20:00`"
                )
                return
            
            day, month, year, hour, minute = map(int, match.groups())
            
            # Проверяем корректность даты и времени
            try:
                event_datetime = datetime(year, month, day, hour, minute)
                if event_datetime < datetime.now():
                    await update.message.reply_text("❌ Дата и время события не могут быть в прошлом!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Неверная дата или время!")
                return
            
        else:
            # Для регулярных событий формат зависит от типа
            if event_type in ['еженедельно', 'двухнедельно']:
                # Формат: ДЕНЬ_ЧЧ:ММ (например: понедельник_21:00, вторник_19:30)
                parts = time_str.split('_', 1)
                if len(parts) != 2:
                    await update.message.reply_text(
                        "❌ Неверный формат времени для еженедельного события!\n"
                        "Используйте формат: ДЕНЬ_ЧЧ:ММ\n"
                        "Например: `понедельник_21:00`, `вторник_19:30`, `суббота_20:00`\n"
                        "Допустимые дни: понедельник, вторник, среда, четверг, пятница, суббота, воскресенье"
                    )
                    return
                
                day_of_week = parts[0].strip().lower()
                time_part = parts[1].strip()
                
                # Проверяем день недели
                valid_days = {
                    'понедельник': 0, 'monday': 0,
                    'вторник': 1, 'tuesday': 1,
                    'среда': 2, 'wednesday': 2,
                    'четверг': 3, 'thursday': 3,
                    'пятница': 4, 'friday': 4,
                    'суббота': 5, 'saturday': 5,
                    'воскресенье': 6, 'sunday': 6
                }
                
                if day_of_week not in valid_days:
                    await update.message.reply_text(
                        "❌ Неверный день недели!\n"
                        "Допустимые дни: понедельник, вторник, среда, четверг, пятница, суббота, воскресенье"
                    )
                    return
                
                # Проверяем формат времени
                time_pattern = r'^(\d{1,2}):(\d{2})$'
                match = re.match(time_pattern, time_part)
                if not match:
                    await update.message.reply_text(
                        "❌ Неверный формат времени!\n"
                        "Используйте формат: ЧЧ:ММ\n"
                        "Например: `21:00`"
                    )
                    return
                
                hour, minute = map(int, match.groups())
                
                # Проверяем корректность времени
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    await update.message.reply_text("❌ Неверное время! Часы должны быть от 0 до 23, минуты от 0 до 59.")
                    return
                
                # Обновляем time_str для сохранения в формате день_время
                time_str = f"{day_of_week}_{time_part}"
                
            elif event_type == 'ежемесячно':
                # Формат: ДД_ЧЧ:ММ (например: 01_21:00, 15_19:30)
                parts = time_str.split('_', 1)
                if len(parts) != 2:
                    await update.message.reply_text(
                        "❌ Неверный формат времени для ежемесячного события!\n"
                        "Используйте формат: ДД_ЧЧ:ММ\n"
                        "Например: `01_21:00`, `15_19:30`, `30_20:00`\n"
                        "День месяца должен быть от 01 до 31"
                    )
                    return
                
                day_of_month = parts[0].strip()
                time_part = parts[1].strip()
                
                try:
                    day_num = int(day_of_month)
                    if not 1 <= day_num <= 31:
                        await update.message.reply_text("❌ День месяца должен быть от 01 до 31!")
                        return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат дня месяца!")
                    return
                
                # Проверяем формат времени
                time_pattern = r'^(\d{1,2}):(\d{2})$'
                match = re.match(time_pattern, time_part)
                if not match:
                    await update.message.reply_text(
                        "❌ Неверный формат времени!\n"
                        "Используйте формат: ЧЧ:ММ\n"
                        "Например: `21:00`"
                    )
                    return
                
                hour, minute = map(int, match.groups())
                
                # Проверяем корректность времени
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    await update.message.reply_text("❌ Неверное время! Часы должны быть от 0 до 23, минуты от 0 до 59.")
                    return
                
                # Обновляем time_str для сохранения в формате день_время
                time_str = f"{day_of_month.zfill(2)}_{time_part}"
                
            else:  # ежедневно
                # Для ежедневных событий формат: ЧЧ:ММ
                time_pattern = r'^(\d{1,2}):(\d{2})$'
                match = re.match(time_pattern, time_str)
                if not match:
                    await update.message.reply_text(
                        "❌ Неверный формат времени!\n"
                        "Используйте формат: ЧЧ:ММ\n"
                        "Например: `21:00`"
                    )
                    return
                
                hour, minute = map(int, match.groups())
                
                # Проверяем корректность времени
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    await update.message.reply_text("❌ Неверное время! Часы должны быть от 0 до 23, минуты от 0 до 59.")
                    return
        
        # Добавляем событие
        if self.bot.settings_manager.add_event(chat_id, event_name, event_type, time_str):
            # Настраиваем событие в JobQueue
            try:
                # Получаем JobQueue через контекст
                if (hasattr(context, 'application') and 
                    hasattr(context.application, 'job_queue') and 
                    context.application.job_queue):
                    
                    self.bot.job_scheduler.setup_event_jobs(
                        chat_id,
                        self.bot.settings_manager,
                        context.application.job_queue,
                        self.bot.job_scheduler.timezone,
                        self.bot
                    )
                    self.logger.info(f"✅ Событие '{event_name}' настроено в JobQueue")
                else:
                    self.logger.warning("⚠️ JobQueue недоступен для настройки события")
            except Exception as e:
                self.logger.error(f"❌ Ошибка настройки события '{event_name}' в JobQueue: {e}")
            
            # Отправляем сообщение об успешном добавлении
            if event_type == 'одноразово':
                response_message = await update.message.reply_text(f"✅ Одноразовое событие '{event_name}' на {time_str} добавлено!")
            elif event_type == 'двухнедельно':
                response_message = await update.message.reply_text(f"✅ Событие '{event_name}' (раз в 2 недели в {time_str}) добавлено!")
            elif event_type == 'ежемесячно':
                response_message = await update.message.reply_text(f"✅ Событие '{event_name}' (ежемесячно в {time_str}) добавлено!")
            else:
                response_message = await update.message.reply_text(f"✅ {event_type.capitalize()}е событие '{event_name}' в {time_str} добавлено!")
            
            # Асинхронно удаляем сообщения через 5 секунд
            asyncio_task = context.application.create_task(
                self._delete_messages_after_delay(
                    context, 
                    chat_id, 
                    [update.message.message_id, response_message.message_id], 
                    delay=5
                )
            )
        else:
            await update.message.reply_text(f"❌ Ошибка при добавлении события '{event_name}'!")
    
    async def _delete_messages_after_delay(self, context, chat_id, message_ids, delay=5):
        """Удаляет указанные сообщения через заданное количество секунд"""
        try:
            import asyncio
            await asyncio.sleep(delay)
            
            for message_id in message_ids:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception as e:
                    self.logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка при удалении сообщений: {e}")

    async def list_events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда просмотра всех событий"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        events = self.bot.settings_manager.get_events_for_group(chat_id)
        
        if not events:
            await update.message.reply_text("❌ В этой группе пока нет событий.")
            return
        
        # Разделяем события по типам
        daily_events = []
        weekly_events = []
        biweekly_events = []
        monthly_events = []
        one_time_events = []
        
        for event_key, data in events.items():
            event_type = data.get('type', '').lower()
            if event_type == 'ежедневно':
                daily_events.append(data)
            elif event_type == 'еженедельно':
                weekly_events.append(data)
            elif event_type == 'двухнедельно':
                biweekly_events.append(data)
            elif event_type == 'ежемесячно':
                monthly_events.append(data)
            elif event_type == 'одноразово':
                one_time_events.append(data)
        
        message = "📅 События в этой группе:\n\n"
        
        # Ежедневные события
        if daily_events:
            message += "Ежедневные события:\n"
            for event in daily_events:
                message += f"• {event['name']} - {event['time']}\n"
            message += "\n"
        
        # Еженедельные события
        if weekly_events:
            message += "Еженедельные события:\n"
            for event in weekly_events:
                message += f"• {event['name']} - {event['time']}\n"
            message += "\n"
        
        # События раз в 2 недели
        if biweekly_events:
            message += "События раз в 2 недели:\n"
            for event in biweekly_events:
                message += f"• {event['name']} - {event['time']}\n"
            message += "\n"
        
        # Ежемесячные события
        if monthly_events:
            message += "Ежемесячные события:\n"
            for event in monthly_events:
                message += f"• {event['name']} - {event['time']}\n"
            message += "\n"
        
        # Одноразовые события
        if one_time_events:
            message += "Одноразовые события:\n"
            for event in one_time_events:
                message += f"• {event['name']} - {event['time']}\n"
            message += "\n"
        
        # Отправляем без форматирования Markdown
        await update.message.reply_text(message)
    
    async def delete_event_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда удаления события"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
"Используйте: `/несобытие НАЗВАНИЕ`\n"
                "Например: `/несобытие Руины`"
            )
            return
        
        event_name = parts[1].strip()
        
        # Удаляем событие
        if self.bot.settings_manager.remove_event(chat_id, event_name):
            await update.message.reply_text(f"✅ Событие '{event_name}' удалено!")
        else:
            await update.message.reply_text(f"❌ Событие '{event_name}' не найдено!")