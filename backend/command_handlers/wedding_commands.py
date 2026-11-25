"""Обработчики команд для работы со свадьбами"""
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from .base_handler import BaseCommandHandler
from backend.file_manager import FileManager

logger = logging.getLogger(__name__)


class WeddingCommands(BaseCommandHandler):
    """Обработчики команд для работы со свадьбами"""
    
    async def add_wedding_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда добавления свадьбы"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=2)  # Разделяем максимум на 3 части (команда + имя + дата)
        
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
                "Используйте: `/свадьба ИМЯ ДД.ММ` или `/свадьба ИМЯ ДД.ММ.ГГГГ`\n"
                "Например: `/свадьба Иван 15.03` или `/свадьба Иван 15.03.2020`"
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
                "Например: `15.03` или `15.03.2020`"
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
        
        # Добавляем свадьбу
        if self.bot.settings_manager.add_wedding(chat_id, name, day, month, year):
            # Настраиваем свадьбу в JobQueue
            if (hasattr(self.bot, 'application') and 
                self.bot.application and 
                hasattr(self.bot.application, 'job_queue') and 
                self.bot.application.job_queue):
                try:
                    self.bot.job_scheduler.setup_wedding_jobs(
                        chat_id,
                        self.bot.settings_manager,
                        self.bot.application.job_queue
                    )
                    logger.info(f"✅ Свадьба '{name}' настроена в JobQueue")
                except Exception as e:
                    logger.error(f"❌ Ошибка настройки свадьбы '{name}' в JobQueue: {e}")
            
            if year:
                await update.message.reply_text(f"✅ Годовщина свадьбы {name} ({day:02d}.{month:02d}.{year}) добавлена!")
            else:
                await update.message.reply_text(f"✅ Годовщина свадьбы {name} ({day:02d}.{month:02d}) добавлена!")
        else:
            await update.message.reply_text(f"❌ Годовщина свадьбы {name} уже существует!")
    
    async def list_weddings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда просмотра свадеб с пагинацией"""
        import asyncio
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        weddings = self.bot.settings_manager.get_weddings_for_group(chat_id)
        
        if not weddings:
            await update.message.reply_text("❌ В этой группе пока нет годовщин свадеб.")
            return
        
        # Сортируем по дате
        sorted_weddings = sorted(
            weddings.items(),
            key=lambda x: (int(x[1]['month']), int(x[1]['day']))
        )
        
        # Названия месяцев на русском
        month_names = [
            "", "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        
        # Разбиваем на страницы по 15 записей
        page_size = 15
        total_pages = (len(sorted_weddings) + page_size - 1) // page_size
        
        for page_num in range(total_pages):
            start_idx = page_num * page_size
            end_idx = min(start_idx + page_size, len(sorted_weddings))
            page_weddings = sorted_weddings[start_idx:end_idx]
            
            # Формируем заголовок страницы
            if total_pages > 1:
                header = f"💍 *Годовщины свадеб в этой группе* (страница {page_num + 1}/{total_pages}):\n\n"
            else:
                header = "💍 *Годовщины свадеб в этой группе:*\n\n"
            
            # Формируем список для текущей страницы
            wedding_list = header
            
            for index, (name_key, data) in enumerate(page_weddings, start=start_idx + 1):
                name = data['name']
                day = int(data['day'])
                month = int(data['month'])
                year = data.get('year')
                
                # Экранируем специальные символы в имени для Markdown
                escaped_name = name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
                
                # Форматируем дату с словесным месяцем
                month_name = month_names[month] if 1 <= month <= 12 else str(month)
                
                if year:
                    # Рассчитываем количество лет
                    from datetime import datetime
                    current_year = datetime.now().year
                    years = current_year - int(year)
                    formatted_date = f"{day} {month_name} {year} ({years} лет)"
                else:
                    formatted_date = f"{day} {month_name}"
                
                wedding_list += f"{index}. {escaped_name} - {formatted_date}\n"
            
            # Добавляем индикатор продолжения если есть еще страницы
            if page_num < total_pages - 1:
                remaining = len(sorted_weddings) - end_idx
                wedding_list += f"\n_еще {remaining} строк в следующем сообщении_"
            
            # Отправляем страницу
            try:
                await update.message.reply_text(wedding_list, parse_mode='Markdown')
                
                # Задержка между страницами (кроме последней)
                if page_num < total_pages - 1:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"Ошибка отправки списка свадеб: {e}")
                await update.message.reply_text("❌ Ошибка при отправке списка!")
                return
    
    async def delete_wedding_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда удаления свадьбы"""
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Проверяем формат команды
        text = update.message.text.strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Неверный формат команды!\n"
"Используйте: `/несвадьба ИМЯ`\n"
                "Например: `/несвадьба Иван`"
            )
            return
        
        name = parts[1].strip()
        
        # Удаляем свадьбу
        if self.bot.settings_manager.remove_wedding(chat_id, name):
            await update.message.reply_text(f"✅ Годовщина свадьбы {name} удалена!")
        else:
            await update.message.reply_text(f"❌ Годовщина свадьбы {name} не найдена!")
    
