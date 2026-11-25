"""Модуль для работы с файлами данных"""
import json
from pathlib import Path
from typing import List, Dict
import logging

from config import config

logger = logging.getLogger(__name__)


class FileManager:
    """Класс для управления файлами данных бота"""
    
    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
    
    def load_congratulations(self) -> List[str]:
        """Загружает поздравления из файла с кэшированием"""
        try:
            cache_key = 'congratulations'
            
            # Проверяем кэш
            if cache_key in self._cache:
                file_mtime = Path(config.CONGRATULATIONS_FILE).stat().st_mtime
                if file_mtime <= self._cache_timestamps.get(cache_key, 0):
                    return self._cache[cache_key]
            
            # Загружаем из файла
            if Path(config.CONGRATULATIONS_FILE).exists():
                with open(config.CONGRATULATIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result = [item['text'] for item in data if 'text' in item]
                    
                    # Обновляем кэш
                    self._cache[cache_key] = result
                    self._cache_timestamps[cache_key] = Path(config.CONGRATULATIONS_FILE).stat().st_mtime
                    
                    return result
            else:
                logger.error(f"Файл {config.CONGRATULATIONS_FILE} не найден!")
                return ["🎂 С днем рождения!"]
        except Exception as e:
            logger.error(f"Ошибка загрузки поздравлений: {e}")
            return ["🎂 С днем рождения!"]
    
    def load_weddings(self) -> List[str]:
        """Загружает свадебные поздравления из файла с кэшированием"""
        try:
            cache_key = 'weddings'
            
            # Проверяем кэш
            if cache_key in self._cache:
                file_mtime = Path(config.WEDDINGS_FILE).stat().st_mtime
                if file_mtime <= self._cache_timestamps.get(cache_key, 0):
                    return self._cache[cache_key]
            
            # Загружаем из файла
            if Path(config.WEDDINGS_FILE).exists():
                with open(config.WEDDINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result = [item['text'] for item in data if 'text' in item]
                    
                    # Обновляем кэш
                    self._cache[cache_key] = result
                    self._cache_timestamps[cache_key] = Path(config.WEDDINGS_FILE).stat().st_mtime
                    
                    return result
            else:
                logger.error(f"Файл {config.WEDDINGS_FILE} не найден!")
                return ["💍 С юбилеем свадьбы!"]
        except Exception as e:
            logger.error(f"Ошибка загрузки свадебных поздравлений: {e}")
            return ["💍 С юбилеем свадьбы!"]
    
    def load_events(self) -> Dict[str, str]:
        """Загружает события из файла с кэшированием"""
        try:
            cache_key = 'events'
            
            # Проверяем кэш
            if cache_key in self._cache:
                file_mtime = Path(config.EVENTS_FILE).stat().st_mtime
                if file_mtime <= self._cache_timestamps.get(cache_key, 0):
                    return self._cache[cache_key]
            
            # Загружаем из файла
            if Path(config.EVENTS_FILE).exists():
                with open(config.EVENTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    events = {}
                    # Новая структура: объект с вложенными объектами
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, dict) and 'text' in value:
                                events[key] = value['text']
                            else:
                                # Для обратной совместимости со старой структурой
                                events[key] = value
                    
                    # Обновляем кэш
                    self._cache[cache_key] = events
                    self._cache_timestamps[cache_key] = Path(config.EVENTS_FILE).stat().st_mtime
                    
                    return events
            else:
                logger.error(f"Файл {config.EVENTS_FILE} не найден!")
                return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки событий: {e}")
            return {}
    
    @staticmethod
    def get_group_file_path(group_name: str) -> Path:
        """Получает путь к файлу группы"""
        return Path(config.GROUPS_FOLDER) / f"{group_name}.json"
    
    @staticmethod
    def load_group_data(group_name: str) -> Dict:
        """Загружает данные для конкретной группы"""
        try:
            file_path = FileManager.get_group_file_path(group_name)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки данных группы {group_name}: {e}")
            return {}
    
    @staticmethod
    def save_group_data(group_name: str, group_data: Dict):
        """Сохраняет данные для конкретной группы"""
        try:
            file_path = FileManager.get_group_file_path(group_name)
            # Создаем папку если её нет
            file_path.parent.mkdir(exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных группы {group_name}: {e}")
    
    @staticmethod
    def load_all_groups() -> Dict:
        """Загружает все группы из отдельных файлов"""
        all_groups = {}
        groups_folder = Path(config.GROUPS_FOLDER)
        
        if not groups_folder.exists():
            return {}
        
        for file_path in groups_folder.glob("*.json"):
            group_name = file_path.stem  # имя файла без расширения
            try:
                # Проверяем, что файл существует и не пустой
                if not file_path.exists():
                    logger.warning(f"Файл {file_path} не существует, пропускаем")
                    continue
                
                if file_path.stat().st_size == 0:
                    logger.warning(f"Файл {file_path} пустой, пропускаем")
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        logger.warning(f"Файл {file_path} содержит только пробельные символы, пропускаем")
                        continue
                    
                    # Проверяем корректность JSON перед парсингом
                    try:
                        json.loads(content)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Некорректный JSON в файле {file_path}: {json_err}")
                        logger.error(f"Содержимое файла: {content[:200]}...")
                        continue
                    
                    # Загружаем данные
                    all_groups[group_name] = json.loads(content)
                    
            except FileNotFoundError:
                logger.warning(f"Файл {file_path} не найден, пропускаем")
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в файле {file_path}: {e}")
                logger.error(f"Позиция ошибки: строка {e.lineno}, столбец {e.colno}")
            except Exception as e:
                logger.error(f"Ошибка загрузки файла {file_path}: {e}")
        
        return all_groups
    
    @staticmethod
    def save_all_groups(groups_data: Dict):
        """Сохраняет все группы в отдельные файлы"""
        for group_name, group_data in groups_data.items():
            FileManager.save_group_data(group_name, group_data)
    
    @staticmethod
    def migrate_from_single_file() -> bool:
        """Мигрирует данные из старого формата в новый (групповые файлы)"""
        try:
            # Проверяем существование старого файла
            old_file = Path('all_settings.json')
            if not old_file.exists():
                logger.info("Старый файл настроек не найден, миграция не требуется")
                return True
            
            # Загружаем старые данные
            with open(old_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            # Извлекаем группы
            groups = old_data.get('groups', {}) if isinstance(old_data, dict) and 'groups' in old_data else old_data
            
            if not groups:
                logger.warning("Нет данных для миграции")
                return True
            
            # Сохраняем каждую группу в отдельный файл
            migrated_count = 0
            for chat_id, group_data in groups.items():
                FileManager.save_group_data(chat_id, group_data)
                migrated_count += 1
                logger.info(f"Мигрирована группа {chat_id}")
            
            logger.info(f"Успешно мигрировано {migrated_count} групп")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка миграции данных: {e}")
            return False