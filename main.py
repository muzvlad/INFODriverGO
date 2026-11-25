#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram бот для дней рождения
Основной файл запуска
"""

import sys
import os
import logging

# Убираем ограничения на вывод в терминале Windows
if sys.platform == "win32":
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 0x0001 | 0x0002 | 0x0004)
    except Exception:
        pass
from datetime import datetime, timedelta
import threading
import time

# Настройка логирования с переводом
from logging import Formatter

class ColoredFormatter(Formatter):
    """Кастомный форматтер с цветами и переводом сообщений"""
    
    # Цвета отключены для снижения нагрузки
    COLORS = {
        'DEBUG': '',
        'INFO': '',
        'WARNING': '',
        'ERROR': '',
        'CRITICAL': ''
    }
    
    # Словарь перевода сообщений
    TRANSLATIONS = {
        'Application started': 'Приложение запущено',
        'Application is stopping': 'Приложение останавливается',
        'Application stopped': 'Приложение остановлено',
        'Starting': 'Запуск',
        'Stopping': 'Остановка',
        'Running': 'Работает',
        'Stopped': 'Остановлено',
        'Added job': 'Добавлено задание',
        'to job store "default"': 'в хранилище заданий "по умолчанию"',
        'All active jobs': 'Все активные задания',
        'group_notification_today_': 'уведомление на сегодня',
        'group_daily_notification_': 'ежедневное уведомление',
        'Removed job': 'Удалено задание',
        'from job store "default"': 'из хранилища заданий "по умолчанию"',
        'Scheduler started': 'Планировщик запущен',
        'Scheduler shutdown': 'Планировщик остановлен',
        'Запуск polling': 'Запуск опроса сообщений'
    }
    
    def format(self, record):
        # Цвета отключены для снижения нагрузки
        level_color = ''
        reset_color = ''
        
        # Переводим сообщение если нужно
        message = record.getMessage()
        for eng, rus in self.TRANSLATIONS.items():
            message = message.replace(eng, rus)
        
        # Исправляем форматирование имен заданий
        if 'Добавлено задание' in message or 'Все активные задания' in message:
            # Исправляем имена заданий: добавляем пробелы и убираем дефисы
            message = message.replace('уведомление на сегодня-', 'уведомление на сегодня - ')
            message = message.replace('ежедневное уведомление-', 'ежедневное уведомление - ')
            message = message.replace('уведомление на сегодня', 'уведомление на сегодня - ')
        
        # Форматируем время
        timestamp = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        
        # Собираем финальную строку (только уровень лога цветной)
        formatted = f'{timestamp} - {level_color}{record.levelname}{reset_color} - {message}'
        return formatted


class DailyLogFileHandler(logging.FileHandler):
    """Обработчик логов с ежедневной записью в файл и автоочисткой"""
    
    MAX_BUFFER_SIZE = 5000  # Максимум логов в буфере
    KEEP_LOGS_DAYS = 7  # Хранить логи 7 дней
    
    def __init__(self, base_filename, mode='a', encoding='utf-8', delay=False):
        self.base_filename = base_filename
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.logs_buffer = []  # Буфер для накопления логов
        self.filename = f"{base_filename}_{self.current_date}.txt"
        self.last_cleanup_date = datetime.now().date()
        super().__init__(self.filename, mode, encoding, delay)
        
        # Запускаем таймер для ежедневной записи и очистки
        self.timer_thread = threading.Thread(target=self._schedule_daily_logging, daemon=True)
        self.timer_thread.start()
        
        print(f"📝 Логи будут записываться в файл: {self.filename}, старые файлы удаляются через 7 дней")
    
    def _should_write_today(self):
        """Проверяет, пора ли записывать логи сегодня (23:59)"""
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_date = now.strftime('%Y-%m-%d')
        
        # Проверяем, что дата совпадает и время 23:59
        return (current_date == self.current_date and 
                current_time == '23:59')
    
    def _write_logs_only(self):
        """Только записывает логи в файл без перезапуска"""
        try:
            if len(self.logs_buffer) > 0:
                # Записываем все накопленные логи в файл
                with open(self.filename, 'a', encoding='utf-8') as f:
                    for log_entry in self.logs_buffer:
                        f.write(log_entry + '\n')
                
                print(f"✅ Логи записаны в файл: {self.filename} ({len(self.logs_buffer)} записей)")
                
                # Меняем имя файла для следующего дня
                self.current_date = datetime.now().strftime('%Y-%m-%d')
                self.filename = f"{self.base_filename}_{self.current_date}.txt"
                
                # Очищаем буфер
                self.logs_buffer.clear()
                
                # Переоткрываем файловый хэндлер с новым именем файла
                self.stream.close()
                self.stream = self._open()
                
        except Exception as e:
            print(f"❌ Ошибка при записи логов: {e}")
    
    def _cleanup_old_logs(self):
        """Удаляет лог-файлы старше KEEP_LOGS_DAYS дней"""
        try:
            import glob
            logs_dir = os.path.dirname(self.base_filename) or "logs"
            pattern = os.path.join(logs_dir, "log_*.txt")
            cutoff_date = datetime.now() - timedelta(days=self.KEEP_LOGS_DAYS)
            deleted_count = 0
            
            for file_path in glob.glob(pattern):
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"🗑️ Удален старый лог: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить {file_path}: {e}")
            
            if deleted_count > 0:
                print(f"✅ Удалено {deleted_count} старых лог-файлов (старше {self.KEEP_LOGS_DAYS} дней)")
            else:
                print(f"✅ Проверка старых логов: файлов для удаления нет")
                
        except Exception as e:
            print(f"❌ Ошибка при очистке старых логов: {e}")
    
    def _schedule_daily_logging(self):
        """Планирует ежедневную запись логов в 23:59 и очистку старых файлов"""
        while True:
            try:
                now = datetime.now()
                current_date = now.date()
                current_time = now.strftime('%H:%M')
                
                # Проверяем, нужно ли записать логи (в 23:59)
                if current_time == '23:59':
                    self._write_logs_only()
                
                # Очищаем старые логи при смене дня
                if current_date != self.last_cleanup_date:
                    self._cleanup_old_logs()
                    self.last_cleanup_date = current_date
                
                # Проверяем каждые 60 секунд (меньше нагрузка)
                time.sleep(60)
            except Exception as e:
                print(f"❌ Ошибка в планировщике логов: {e}")
                time.sleep(60)
    
    def emit(self, record):
        """Переопределяем emit для накопления логов в буфер с ограничением размера"""
        try:
            # Очищаем старые логи если буфер переполнен
            if len(self.logs_buffer) >= self.MAX_BUFFER_SIZE:
                # Оставляем только последние 1000 записей
                self.logs_buffer = self.logs_buffer[-1000:]
            
            # Форматируем запись лога
            msg = self.format(record)
            # Добавляем в буфер вместо немедленной записи
            self.logs_buffer.append(msg)
        except Exception:
            self.handleError(record)


def setup_logging_with_rotation():
    """Настраивает логирование с ротацией файлов"""
    # Настраиваем логирование с уровнем INFO для отображения команд
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Наш логгер показывает INFO и выше
    
    # Применяем кастомный форматтер ко всем хендлерам
    formatter = ColoredFormatter()
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
    
    # Создаем папку logs если её нет
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Добавляем обработчик для записи логов в файлы с ротацией
    file_handler = DailyLogFileHandler(os.path.join(logs_dir, "log"))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.root.addHandler(file_handler)
    
    # Подавляем избыточные логи от сетевых библиотек
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Подавляем избыточные логи при запуске
    logging.getLogger('tzlocal').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Подавляем избыточные DEBUG логи от Telegram
    logging.getLogger('telegram.ext.Updater').setLevel(logging.WARNING)
    logging.getLogger('telegram.request').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)  # Основной уровень для telegram
    
    # Подавляем избыточные логи при запуске
    logging.getLogger('backend.scheduler.job_scheduler').setLevel(logging.WARNING)
    logging.getLogger('backend.scheduler.event_scheduler').setLevel(logging.WARNING)
    logging.getLogger('backend.scheduler.wedding_scheduler').setLevel(logging.WARNING)
    
    return logger


# Настраиваем логирование с ротацией
logger = setup_logging_with_rotation()


def main():
    """Главная функция запуска бота"""
    try:
        # Импортируем конфигурацию
        from config import config
        
        # Проверяем конфигурацию
        config.validate()
        
        # Импортируем бота из backend
        from backend.main_bot import MainBot
        
        # Создаем и запускаем бота
        bot = MainBot()
        bot.run()
        
    except ValueError as e:
        print(str(e))
        print("\n📝 Создайте файл .env со следующим содержимым:")
        print("BOT_TOKEN=ваш_токен_бота")
        print("TIMEZONE=Europe/Moscow")
        return 1
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"❌ Непредвиденная ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())