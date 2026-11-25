"""Обработчики команд для работы с днями рождения"""
import logging
import re
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes
from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class BirthdayCommands(BaseCommandHandler):
    """Обработчики команд для работы с днями рождения"""
    
    async def add_birthday_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда добавления дня рождения"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=2)  # Разделяем максимум на 3 части (команда + имя + дата)
        
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
                "Используйте: `/добавить ИМЯ ДД.ММ` или `/добавить ИМЯ ДД.ММ.ГГГГ`\n"
                "Например: `/добавить Иван 15.03` или `/добавить Иван 15.03.1990`"
            )
            return
        
        name = parts[1].strip()
        date_str = parts[2].strip()
        
        # Проверяем формат даты
        date_pattern = r'^(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?$'
        match = re.match(date_pattern, date_str)
        
        if not match:
            await update.message.reply_text(
                "❌ Неверный формат даты!\n"
                "Используйте формат ДД.ММ или ДД.ММ.ГГГГ\n"
                "Например: `15.03` или `15.03.1990`"
            )
            return
        
        day, month = int(match.group(1)), int(match.group(2))
        year = int(match.group(3)) if match.group(3) else None
        
        # Проверяем корректность даты
        try:
            if year:
                datetime(year, month, day)
            else:
                # Для дат без года проверяем только день и месяц
                if not (1 <= day <= 31 and 1 <= month <= 12):
                    raise ValueError("Неверная дата")
        except ValueError:
            await update.message.reply_text("❌ Неверная дата!")
            return
        
        # Добавляем день рождения
        if self.bot.settings_manager.add_birthday(chat_id, name, day, month, year):
            if year:
                await update.message.reply_text(f"✅ День рождения {name} ({day:02d}.{month:02d}.{year}) добавлен!")
            else:
                await update.message.reply_text(f"✅ День рождения {name} ({day:02d}.{month:02d}) добавлен!")
        else:
            await update.message.reply_text(f"❌ День рождения {name} уже существует!")
    
    async def list_birthdays_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда просмотра дней рождения с пагинацией"""
        import asyncio
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
        
        if not birthdays:
            await update.message.reply_text("❌ В этой группе пока нет дней рождения.")
            return
        
        # Сортируем по дате
        sorted_birthdays = sorted(
            birthdays.items(),
            key=lambda x: (int(x[1]['month']), int(x[1]['day']))
        )
        
        # Названия месяцев на русском
        month_names = [
            "", "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        
        # Разбиваем на страницы по 15 записей
        page_size = 15
        total_pages = (len(sorted_birthdays) + page_size - 1) // page_size
        
        for page_num in range(total_pages):
            start_idx = page_num * page_size
            end_idx = min(start_idx + page_size, len(sorted_birthdays))
            page_birthdays = sorted_birthdays[start_idx:end_idx]
            
            # Формируем заголовок страницы
            if total_pages > 1:
                header = f"🎂 *Дни рождения в этой группе* (страница {page_num + 1}/{total_pages}):\n\n"
            else:
                header = "🎂 *Дни рождения в этой группе:*\n\n"
            
            # Формируем список для текущей страницы
            birthday_list = header
            
            for index, (name_key, data) in enumerate(page_birthdays, start=start_idx + 1):
                name = data['name']
                day = int(data['day'])
                month = int(data['month'])
                year = data.get('year')
                
                # Экранируем специальные символы в имени для Markdown
                escaped_name = name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
                
                # Форматируем дату с словесным месяцем
                month_name = month_names[month] if 1 <= month <= 12 else str(month)
                
                if year:
                    # Рассчитываем возраст
                    from datetime import datetime
                    current_year = datetime.now().year
                    age = current_year - int(year)
                    formatted_date = f"{day} {month_name} {year} (Возраст: {age})"
                else:
                    formatted_date = f"{day} {month_name}"
                
                birthday_list += f"{index}. {escaped_name} - {formatted_date}\n"
            
            # Добавляем индикатор продолжения если есть еще страницы
            if page_num < total_pages - 1:
                remaining = len(sorted_birthdays) - end_idx
                birthday_list += f"\n_еще {remaining} строк в следующем сообщении_"
            
            # Отправляем страницу
            try:
                await update.message.reply_text(birthday_list, parse_mode='Markdown')
                
                # Задержка между страницами (кроме последней)
                if page_num < total_pages - 1:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"Ошибка отправки списка дней рождения: {e}")
                await update.message.reply_text("❌ Ошибка при отправке списка!")
                return
    
    async def delete_birthday_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда удаления дня рождения"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
                "Используйте: `/удалить ИМЯ`\n"
                "Например: `/удалить Иван`"
            )
            return
        
        name = parts[1].strip()
        
        # Удаляем день рождения
        if self.bot.settings_manager.remove_birthday(chat_id, name):
            await update.message.reply_text(f"✅ День рождения {name} удален!")
        else:
            await update.message.reply_text(f"❌ День рождения {name} не найден!")
    
    async def today_birthdays_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда просмотра сегодняшних дней рождения"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
        
        if not birthdays:
            await update.message.reply_text("❌ В этой группе пока нет дней рождения.")
            return
        
        # Получаем сегодняшнюю дату
        today = datetime.now().date()
        today_day = today.day
        today_month = today.month
        
        # Ищем сегодняшние дни рождения
        today_birthdays = []
        for name_key, data in birthdays.items():
            day = int(data['day'])
            month = int(data['month'])
            
            if day == today_day and month == today_month:
                today_birthdays.append(data['name'])
        
        if not today_birthdays:
            await update.message.reply_text("📅 Сегодня нет дней рождения.")
            return
        
        # Формируем сообщение
        if len(today_birthdays) == 1:
            message = f"🎉 Сегодня день рождения у {today_birthdays[0]}! 🎂"
        else:
            names = ", ".join(today_birthdays)
            message = f"🎉 Сегодня день рождения у: {names}! 🎂"
        
        await update.message.reply_text(message)
    
    async def upcoming_birthdays_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда просмотра ближайших дней рождения (на 7 дней вперед)"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        birthdays = self.bot.settings_manager.get_birthdays_for_group(chat_id)
        
        if not birthdays:
            await update.message.reply_text("❌ В этой группе пока нет дней рождения.")
            return
        
        # Названия месяцев
        month_names = [
            "", "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        
        # Получаем текущую дату
        today = datetime.now()
        
        # Создаем список с датами для сортировки
        birthday_list = []
        for name_key, data in birthdays.items():
            day = int(data['day'])
            month = int(data['month'])
            
            # Рассчитываем дни до дня рождения
            birthday_this_year = date(today.year, month, day)
            
            # Если день рождения уже прошел в этом году, берем следующий год
            if birthday_this_year < today.date():
                birthday_this_year = date(today.year + 1, month, day)
            
            days_until = (birthday_this_year - today.date()).days
            # Только дни рождения в ближайшие 7 дней
            if days_until <= 7:
                birthday_list.append({
                    'name': data['name'],
                    'day': day,
                    'month': month,
                    'days_until': days_until
                })
        
        if not birthday_list:
            await update.message.reply_text("📅 В ближайшие 7 дней дней рождения нет.")
            return
        
        # Сортируем по дням до дня рождения
        birthday_list.sort(key=lambda x: x['days_until'])
        
        message = "🎂 *Ближайшие дни рождения (7 дней):*\n\n"
        
        for index, person in enumerate(birthday_list, start=1):
            name = person['name']
            day = person['day']
            month = person['month']
            days_until = person['days_until']
            
            # Форматируем месяц словами
            month_name = month_names[month] if 1 <= month <= 12 else str(month)
            formatted_date = f"{day} {month_name}"
            
            if days_until == 0:
                message += f"{index}. {name} - сегодня! 🎉\n"
            elif days_until == 1:
                message += f"{index}. {name} - завтра ({formatted_date}) 🎈\n"
            else:
                message += f"{index}. {name} - через {days_until} дн. ({formatted_date})\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')