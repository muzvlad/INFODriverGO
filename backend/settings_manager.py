#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Управление настройками для всех групп
"""

import json
from pathlib import Path
from datetime import time
import logging

logger = logging.getLogger(__name__)


class GroupSettings:
    """Настройки для конкретной группы"""
    
    def __init__(self, chat_id: str, chat_name: str = "Неизвестная группа"):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name
        self.notifications_enabled = False
        self.notification_time = time(hour=19, minute=25)  # По умолчанию 19:25
        self.timezone = "Europe/Moscow"
        self.last_updated = None
    
    def to_dict(self):
        """Преобразует настройки в словарь"""
        result = {
            'chat_name': self.chat_name,
            'notifications_enabled': self.notifications_enabled,
            'notification_time': self.notification_time.strftime('%H:%M'),
            'timezone': self.timezone,
            'last_updated': self.last_updated
        }
        
        # Добавляем динамические атрибуты, если они есть
        if hasattr(self, 'birthdays'):
            result['birthdays'] = self.birthdays
        if hasattr(self, 'weddings'):
            result['weddings'] = self.weddings
        if hasattr(self, 'events'):
            result['events'] = self.events
        
        return result
    
    @classmethod
    def from_dict(cls, chat_id: str, data: dict):
        """Создает объект из словаря"""
        settings = cls(chat_id, data.get('chat_name', 'Неизвестная группа'))
        settings.notifications_enabled = data.get('notifications_enabled', False)
        
        # Парсим время
        time_str = data.get('notification_time', '19:25')
        hour, minute = map(int, time_str.split(':'))
        settings.notification_time = time(hour=hour, minute=minute)
        
        settings.timezone = data.get('timezone', 'Europe/Moscow')
        settings.last_updated = data.get('last_updated')
        
        # Восстанавливаем динамические атрибуты
        if 'birthdays' in data:
            settings.birthdays = data['birthdays']
        if 'weddings' in data:
            settings.weddings = data['weddings']
        if 'events' in data:
            settings.events = data['events']
        
        return settings
    
    def update_chat_name(self, chat_name: str):
        """Обновляет название группы"""
        if chat_name and chat_name != self.chat_name:
            self.chat_name = chat_name
            return True
        return False


class AllSettings:
    """Управление настройками всех групп"""
    
    def __init__(self):
        from backend.file_manager import FileManager
        self.file_manager = FileManager()
        self.group_settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Загружает настройки из файлов групп"""
        try:
            return self.file_manager.load_all_groups()
        except Exception as e:
            print(f"❌ Ошибка загрузки настроек: {e}")
            return {}
    
    def _save_settings(self):
        """Сохраняет настройки в файлы групп"""
        try:
            self.file_manager.save_all_groups(self.group_settings)
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
    
    def _get_current_timestamp(self):
        """Получает текущую метку времени"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_group_settings(self, chat_id: str, chat_name: str = None) -> GroupSettings:
        """Получает настройки для группы (создает если нет)"""
        chat_id_str = str(chat_id)
        
        if chat_id_str not in self.group_settings:
            # Создаем новые настройки по умолчанию
            chat_name = chat_name or f"Группа {chat_id_str}"
            new_settings = GroupSettings(chat_id_str, chat_name)
            self.group_settings[chat_id_str] = new_settings.to_dict()
            self._save_settings()
            return new_settings
        
        # Загружаем существующие настройки
        data = self.group_settings[chat_id_str]
        settings = GroupSettings.from_dict(chat_id_str, data)
        
        # Обновляем название группы если нужно
        if chat_name and chat_name != settings.chat_name:
            settings.update_chat_name(chat_name)
            self.save_group_settings(chat_id_str, settings)
        
        return settings
    
    def save_group_settings(self, chat_id: str, settings: GroupSettings):
        """Сохраняет настройки для группы (НЕМЕДЛЕННО)"""
        chat_id_str = str(chat_id)
        settings.last_updated = self._get_current_timestamp()
        self.group_settings[chat_id_str] = settings.to_dict()
        self._save_settings()  # Сохраняем немедленно!
    
    def is_notifications_enabled(self, chat_id: str) -> bool:
        """Проверяет включены ли уведомления для группы"""
        settings = self.get_group_settings(chat_id)
        return settings.notifications_enabled
    
    def get_notification_time(self, chat_id: str) -> time:
        """Получает время уведомлений для группы"""
        settings = self.get_group_settings(chat_id)
        return settings.notification_time
    
    def set_notification_time(self, chat_id: str, time_str: str) -> bool:
        """Устанавливает время уведомлений для группы"""
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False
            
            settings = self.get_group_settings(chat_id)
            settings.notification_time = time(hour=hour, minute=minute)
            self.save_group_settings(chat_id, settings)
            return True
        except:
            return False
    
    def enable_notifications(self, chat_id: str):
        """Включает уведомления для группы"""
        settings = self.get_group_settings(chat_id)
        settings.notifications_enabled = True
        self.save_group_settings(chat_id, settings)
    
    def disable_notifications(self, chat_id: str):
        """Выключает уведомления для группы"""
        settings = self.get_group_settings(chat_id)
        settings.notifications_enabled = False
        self.save_group_settings(chat_id, settings)
    
    def get_all_groups(self) -> dict:
        """Получает список всех групп с настройками"""
        return self.group_settings
    
    def get_groups_with_notifications(self) -> list:
        """Получает список групп с включенными уведомлениями"""
        result = []
        for chat_id_str, data in self.group_settings.items():
            if data.get('notifications_enabled', False):
                result.append(chat_id_str)
        return result
    
    def update_group_info(self, chat_id: str, chat_name: str = None) -> bool:
        """Обновляет информацию о группе"""
        if chat_name:
            settings = self.get_group_settings(chat_id)
            updated = settings.update_chat_name(chat_name)
            if updated:
                self.save_group_settings(chat_id, settings)
            return updated
        return False
    
    def get_group_info(self, chat_id: str) -> dict:
        """Получает полную информацию о группе"""
        if chat_id in self.group_settings:
            return self.group_settings[chat_id]
        return None
    
    def get_statistics(self) -> dict:
        """Получает статистику по группам"""
        total = len(self.group_settings)
        with_notifications = len(self.get_groups_with_notifications())
        
        return {
            'total_groups': total,
            'groups_with_notifications': with_notifications,
            'groups_without_notifications': total - with_notifications,
            'last_updated': self._get_current_timestamp()
        }
    
    def migrate_from_single_file(self) -> bool:
        """Мигрирует данные из старого формата в новый (групповые файлы)"""
        return self.file_manager.migrate_from_single_file()
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ДНЯМИ РОЖДЕНИЯ ===
    
    def add_birthday(self, chat_id: str, name: str, day: int, month: int, year: int = None) -> bool:
        """Добавляет день рождения в группу"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            settings = self.get_group_settings(chat_id_str)
            
            # Добавляем день рождения
            if not hasattr(settings, 'birthdays'):
                settings.birthdays = {}
            
            birthday_key = name.lower().strip()
            
            # Проверяем, существует ли уже такой день рождения
            if birthday_key in settings.birthdays:
                return False
            
            # Сохраняем день рождения
            birthday_data = {
                'day': day,
                'month': month,
                'name': name
            }
            
            if year:
                birthday_data['year'] = year
            
            settings.birthdays[birthday_key] = birthday_data
            
            # Сохраняем изменения
            self.save_group_settings(chat_id_str, settings)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении дня рождения: {e}")
            return False
    
    def remove_birthday(self, chat_id: str, name: str) -> bool:
        """Удаляет день рождения из группы"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            if chat_id_str not in self.group_settings:
                return False
            
            data = self.group_settings[chat_id_str]
            
            # Проверяем наличие дней рождения
            if 'birthdays' not in data:
                return False
            
            birthday_key = name.lower().strip()
            
            # Удаляем день рождения
            if birthday_key in data['birthdays']:
                del data['birthdays'][birthday_key]
                self._save_settings()
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при удалении дня рождения: {e}")
            return False
    
    def get_birthdays_for_group(self, chat_id: str) -> dict:
        """Получает список дней рождения для группы"""
        try:
            chat_id_str = str(chat_id)
            
            if chat_id_str not in self.group_settings:
                return {}
            
            data = self.group_settings[chat_id_str]
            return data.get('birthdays', {})
            
        except Exception as e:
            print(f"❌ Ошибка при получении дней рождения: {e}")
            return {}
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ СО СВАДЬБАМИ ===
    
    def add_wedding(self, chat_id: str, name: str, day: int, month: int, year: int = None) -> bool:
        """Добавляет годовщину свадьбы в группу"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            settings = self.get_group_settings(chat_id_str)
            
            # Добавляем свадьбу
            if not hasattr(settings, 'weddings'):
                settings.weddings = {}
            
            wedding_key = name.lower().strip()
            
            # Проверяем, существует ли уже такая свадьба
            if wedding_key in settings.weddings:
                return False
            
            # Сохраняем свадьбу
            wedding_data = {
                'day': day,
                'month': month,
                'name': name
            }
            
            if year:
                wedding_data['year'] = year
            
            settings.weddings[wedding_key] = wedding_data
            
            # Сохраняем изменения
            self.save_group_settings(chat_id_str, settings)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении свадьбы: {e}")
            return False
    
    def remove_wedding(self, chat_id: str, name: str) -> bool:
        """Удаляет годовщину свадьбы из группы"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            if chat_id_str not in self.group_settings:
                return False
            
            data = self.group_settings[chat_id_str]
            
            # Проверяем наличие свадеб
            if 'weddings' not in data:
                return False
            
            wedding_key = name.lower().strip()
            
            # Удаляем свадьбу
            if wedding_key in data['weddings']:
                del data['weddings'][wedding_key]
                self._save_settings()
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при удалении свадьбы: {e}")
            return False
    
    def get_weddings_for_group(self, chat_id: str) -> dict:
        """Получает список свадеб для группы"""
        try:
            chat_id_str = str(chat_id)
            
            if chat_id_str not in self.group_settings:
                return {}
            
            data = self.group_settings[chat_id_str]
            return data.get('weddings', {})
            
        except Exception as e:
            print(f"❌ Ошибка при получении свадеб: {e}")
            return {}
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С СОБЫТИЯМИ ===
    
    def add_event(self, chat_id: str, name: str, event_type: str, time_str: str) -> bool:
        """Добавляет событие в группу"""
        try:
            chat_id_str = str(chat_id)
            logger.info(f"Добавляем событие '{name}' типа '{event_type}' в группу {chat_id_str}")
            
            # Получаем настройки группы
            settings = self.get_group_settings(chat_id_str)
            logger.info("Получены настройки группы")
            
            # Добавляем событие
            if not hasattr(settings, 'events'):
                settings.events = {}
                logger.info("Создан пустой словарь events")
            
            event_key = name.lower().strip()
            logger.info(f"Ключ события: '{event_key}'")
            
            # Проверка на существующее событие отключена - разрешаем создание событий с одинаковыми названиями
            # if hasattr(settings, 'events') and event_key in settings.events:
            #     logger.info(f"Событие '{event_key}' уже существует")
            #     return False
            
            # Загружаем текст события из файла events.json
            from backend.file_manager import FileManager
            file_manager = FileManager()
            events_data = file_manager.load_events()
            logger.info(f"Загружены события из файла: {list(events_data.keys())}")
            
            # Ищем текст события
            event_text = None
            if event_key in events_data:
                event_info = events_data[event_key]
                if isinstance(event_info, dict) and 'text' in event_info:
                    event_text = event_info['text']
                else:
                    event_text = event_info
                logger.info(f"Найден текст события: '{event_text}'")
            else:
                logger.info(f"Текст события не найден для ключа '{event_key}'")
            
            # Сохраняем событие
            event_data = {
                'name': name,
                'type': event_type,
                'time': time_str
            }
            
            # Добавляем текст, если найден
            if event_text:
                event_data['text'] = event_text
                logger.info("Добавлен текст в event_data")
            
            settings.events[event_key] = event_data
            logger.info("Событие добавлено в settings.events")
            
            # Сохраняем изменения
            self.save_group_settings(chat_id_str, settings)
            logger.info("Настройки сохранены")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении события: {e}")
            return False
    
    def remove_event(self, chat_id: str, name: str) -> bool:
        """Удаляет событие из группы"""
        try:
            chat_id_str = str(chat_id)
            
            # Получаем настройки группы
            if chat_id_str not in self.group_settings:
                return False
            
            data = self.group_settings[chat_id_str]
            
            # Проверяем наличие событий
            if 'events' not in data:
                return False
            
            event_key = name.lower().strip()
            
            # Удаляем событие
            if event_key in data['events']:
                del data['events'][event_key]
                self._save_settings()
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при удалении события: {e}")
            return False
    
    def get_events_for_group(self, chat_id: str) -> dict:
        """Получает список событий для группы"""
        try:
            chat_id_str = str(chat_id)
            
            if chat_id_str not in self.group_settings:
                return {}
            
            data = self.group_settings[chat_id_str]
            return data.get('events', {})
            
        except Exception as e:
            print(f"❌ Ошибка при получении событий: {e}")
            return {}