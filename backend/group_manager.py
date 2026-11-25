"""Модуль для управления информацией о группах"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class GroupManager:
    """Класс для управления информацией о группах"""
    
    def __init__(self):
        self.group_names_cache: Dict[str, str] = {}
    
    def load_group_names_cache(self, settings_manager):
        """Загружает кэш названий групп из настроек"""
        all_groups = settings_manager.get_all_groups()
        for chat_id_str, data in all_groups.items():
            chat_name = data.get('chat_name', f"Группа {chat_id_str}")
            self.group_names_cache[chat_id_str] = chat_name
        logger.info(f"📋 Загружено {len(self.group_names_cache)} названий групп в кэш")
    
    def update_group_name_cache(self, chat_id: str, chat_name: str, settings_manager):
        """Обновляет кэш названий групп"""
        chat_id_str = str(chat_id)
        if chat_name and chat_name != self.group_names_cache.get(chat_id_str):
            self.group_names_cache[chat_id_str] = chat_name
            # Немедленно обновляем в настройках
            settings_manager.update_group_info(chat_id_str, chat_name)
    
    def get_group_name(self, chat_id: str, default: str = "Неизвестная группа") -> str:
        """Получает название группы из кэша или настроек"""
        chat_id_str = str(chat_id)
        
        # Сначала проверяем кэш
        if chat_id_str in self.group_names_cache:
            return self.group_names_cache[chat_id_str]
        
        # Если и там нет, возвращаем дефолт
        return default
    
    def update_group_info_from_chat(self, update, settings_manager):
        """Обновляет информацию о группе из объекта чата"""
        chat = update.effective_chat
        if not chat:
            return
        
        chat_id = str(chat.id)
        
        # Получаем название группы
        chat_name = None
        if hasattr(chat, 'title') and chat.title:
            chat_name = chat.title
        elif chat.type == 'private':
            if hasattr(chat, 'first_name') and chat.first_name:
                chat_name = f"Личный чат с {chat.first_name}"
                if hasattr(chat, 'last_name') and chat.last_name:
                    chat_name += f" {chat.last_name}"
        
        # Обновляем кэш и настройки
        if chat_name:
            self.update_group_name_cache(chat_id, chat_name, settings_manager)