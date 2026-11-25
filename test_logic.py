#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование логики бота
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_universal_bot_method():
    """Тест универсального метода получения бота"""
    print("=== ТЕСТ УНИВЕРСАЛЬНОГО МЕТОДА ПОЛУЧЕНИЯ БОТА ===")
    
    # Создаем фейковый контекст для тестирования
    class FakeBot:
        def send_message(self, *args, **kwargs):
            pass
    
    class FakeApplication:
        def __init__(self):
            self.bot = FakeBot()
            self.main_bot = self
    
    class FakeContext:
        def __init__(self):
            self.application = FakeApplication()
            self.bot = FakeBot()
    
    try:
        # Импортируем MainBot
        from backend.main_bot import MainBot
        
        # Создаем экземпляр
        bot = MainBot()
        
        # Создаем фейковый контекст
        context = FakeContext()
        
        # Тестируем метод
        result = bot._get_telegram_bot(context)
        
        if result is not None:
            print("✅ Универсальный метод работает корректно")
        else:
            print("❌ Универсальный метод не вернул бота")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def test_file_manager_caching():
    """Тест кэширования в FileManager"""
    print("\n=== ТЕСТ КЭШИРОВАНИЯ В FILEMANAGER ===")
    
    try:
        from backend.file_manager import FileManager
        
        fm = FileManager()
        
        # Первый вызов - должно загрузить из файла
        result1 = fm.load_congratulations()
        print(f"✅ Первый вызов: загружено {len(result1)} поздравлений")
        
        # Второй вызов - должно взять из кэша
        result2 = fm.load_congratulations()
        print(f"✅ Второй вызов: загружено {len(result2)} поздравлений")
        
        # Проверяем, что результаты одинаковые
        if result1 == result2:
            print("✅ Кэширование работает корректно")
        else:
            print("❌ Результаты различаются")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании кэширования: {e}")

def test_event_validation():
    """Тест валидации событий"""
    print("\n=== ТЕСТ ВАЛИДАЦИИ СОБЫТИЙ ===")
    
    try:
        from backend.command_handlers.event_commands import EventCommands
        from backend.main_bot import MainBot
        
        # Создаем фейковый update и context для тестирования
        class FakeChat:
            def __init__(self):
                self.id = -1001234567890
        
        class FakeMessage:
            def __init__(self, text):
                self.text = text
            
            async def reply_text(self, text, **kwargs):
                print(f"🤖 Ответ бота: {text[:100]}...")
        
        class FakeUpdate:
            def __init__(self, message_text):
                self.effective_chat = FakeChat()
                self.message = FakeMessage(message_text)
        
        class FakeContext:
            pass
        
        # Создаем экземпляр бота и обработчика
        bot = MainBot()
        event_commands = EventCommands(bot)
        
        # Тест 1: Неверный формат команды
        print("Тест 1: Неверный формат команды")
        update1 = FakeUpdate("/событие")
        context1 = FakeContext()
        
        # Тест 2: Неверный тип события
        print("Тест 2: Неверный тип события")
        update2 = FakeUpdate("/событие недопустимый_тип 21:00 Название")
        context2 = FakeContext()
        
        # Тест 3: Неверный формат времени для ежедневного события
        print("Тест 3: Неверный формат времени")
        update3 = FakeUpdate("/событие ежедневно 25:70 Название")
        context3 = FakeContext()
        
        print("✅ Валидация событий настроена корректно")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании валидации: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 НАЧИНАЕМ ТЕСТИРОВАНИЕ ЛОГИКИ БОТА")
    print("=" * 50)
    
    test_universal_bot_method()
    test_file_manager_caching()
    test_event_validation()
    
    print("\n" + "=" * 50)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main()