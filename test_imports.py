#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый файл для проверки импортов
"""

print("Начинаем тестирование импортов...")

try:
    print("1. Тестируем импорт config...")
    from config import config
    print("✅ config импортирован успешно")
    
    print("2. Тестируем импорт FileManager...")
    from backend.file_manager import FileManager
    print("✅ FileManager импортирован успешно")
    
    print("3. Тестируем импорт SettingsManager...")
    from backend.settings_manager import AllSettings
    print("✅ SettingsManager импортирован успешно")
    
    print("4. Тестируем импорт команд...")
    from backend.command_handlers.birthday_commands import BirthdayCommands
    from backend.command_handlers.wedding_commands import WeddingCommands
    from backend.command_handlers.event_commands import EventCommands
    from backend.command_handlers.status_handlers import StatusHandlers
    print("✅ Команды импортированы успешно")
    
    print("5. Тестируем импорт JobScheduler...")
    from backend.scheduler.job_scheduler import JobScheduler
    print("✅ JobScheduler импортирован успешно")
    
    print("6. Тестируем импорт BirthdayBot...")
    from backend.main_bot import MainBot
    print("✅ BirthdayBot импортирован успешно")
    
    print("\n🎉 Все импорты прошли успешно!")
    
except Exception as e:
    print(f"❌ Ошибка при импорте: {e}")