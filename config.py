#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация бота
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    # Токен бота из .env файла
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Часовой пояс (по умолчанию Москва)
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
    
    # Имя администратора
    ADMIN_USERNAME = 'muzvlad911'
    
    # Файлы данных
    WISHES_FOLDER = 'wishes'
    CONGRATULATIONS_FILE = 'wishes/congratulations.json'
    WEDDINGS_FILE = 'wishes/weddings.json'
    EVENTS_FILE = 'wishes/events.json'
    GROUPS_FOLDER = 'groups'
    
    @classmethod
    def validate(cls):
        """Проверяем корректность конфигурации"""
        if not cls.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не найден! Создайте файл .env с токеном бота.")
        
        required_files = [cls.CONGRATULATIONS_FILE]
        for file in required_files:
            if not Path(file).exists():
                raise FileNotFoundError(f"❌ Файл {file} не найден!")
        
        return True


# Создаем экземпляр конфигурации
config = Config()