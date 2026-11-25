#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест команды добавления событий
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_event_command():
    """Тест команды добавления события"""
    print("=== ТЕСТ КОМАНДЫ ДОБАВЛЕНИЯ СОБЫТИЯ ===")
    
    try:
        from backend.command_handlers.event_commands import EventCommands
        from backend.main_bot import MainBot
        
        # Создаем фейковые классы для тестирования
        class FakeBot:
            def __init__(self):
                from backend.settings_manager import AllSettings
                self.settings_manager = AllSettings()
                from backend.scheduler.job_scheduler import JobScheduler
                import pytz
                self.job_scheduler = JobScheduler(pytz.timezone('Europe/Moscow'))
        
        class FakeChat:
            def __init__(self):
                self.id = -1001234567890
        
        class FakeMessage:
            def __init__(self, text):
                self.text = text
                self.reply_calls = []
            
            async def reply_text(self, text, **kwargs):
                self.reply_calls.append(text)
                print(f"🤖 Бот ответил: {text}")
        
        class FakeUpdate:
            def __init__(self, message_text):
                self.effective_chat = FakeChat()
                self.message = FakeMessage(message_text)
        
        class FakeContext:
            def __init__(self):
                self.application = None
        
        # Создаем экземпляры
        bot = FakeBot()
        event_commands = EventCommands(bot)
        update = FakeUpdate("/событие ежедневно 19:55 ruins")
        context = FakeContext()
        
        # Выполняем команду
        print("Выполняем команду: /событие ежедневно 19:55 ruins")
        await event_commands.add_event_command(update, context)
        
        # Проверяем результат
        if update.message.reply_calls:
            last_reply = update.message.reply_calls[-1]
            if "добавлено" in last_reply or "настроено" in last_reply:
                print("✅ Команда события работает корректно")
            else:
                print(f"❌ Неожиданный ответ: {last_reply}")
        else:
            print("❌ Команда не вернула ответ")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании команды события: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция"""
    import asyncio
    print("🚀 ТЕСТИРОВАНИЕ КОМАНДЫ СОБЫТИЙ")
    print("=" * 50)
    
    asyncio.run(test_event_command())
    
    print("\n" + "=" * 50)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main()