#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка наличия всех файлов
"""

import os
import sys

def main():
    required_files = [
        'main.py',
        'config.py',
        'help_text.py',
        'wishes/congratulations.json',
        'wishes/events.json',
        'wishes/weddings.json',
        '.env'
    ]
    
    # Очищаем экран
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("ПРОВЕРКА ФАЙЛОВ ДЛЯ БОТА")
    print("=" * 50)
    
    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - НЕ НАЙДЕН!")
            all_ok = False
    
    print("=" * 50)
    
    # Проверка содержимого файлов
    print("\n📋 ПРОВЕРКА СОДЕРЖИМОГО:")
    print("-" * 50)
    
    # Проверка .env
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'BOT_TOKEN=' in content:
                    token_line = [line for line in content.split('\n') if 'BOT_TOKEN=' in line][0]
                    token_value = token_line.split('=')[1].strip()
                    if token_value == 'ВАШ_ТОКЕН_БОТА' or not token_value:
                        print("⚠️  В .env токен не настроен (используется значение по умолчанию)")
                    else:
                        print(f"✅ .env: токен настроен ({token_value[:10]}...)")
                else:
                    print("❌ .env: BOT_TOKEN не найден")
        except Exception as e:
            print(f"❌ .env: ошибка чтения - {e}")
    
    # Проверка help_text.py
    if os.path.exists('help_text.py'):
        try:
            with open('help_text.py', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'HELP_TEXT =' in content and 'START_TEXT =' in content and 'SETTINGS_TEXT =' in content:
                    print("✅ help_text.py: содержит все необходимые переменные")
                else:
                    missing = []
                    if 'HELP_TEXT =' not in content:
                        missing.append('HELP_TEXT')
                    if 'START_TEXT =' not in content:
                        missing.append('START_TEXT')
                    if 'SETTINGS_TEXT =' not in content:
                        missing.append('SETTINGS_TEXT')
                    print(f"❌ help_text.py: отсутствуют переменные: {', '.join(missing)}")
                    all_ok = False
        except Exception as e:
            print(f"❌ help_text.py: ошибка чтения - {e}")
            all_ok = False
    
    # Проверка файлов в папке wishes
    if os.path.exists('wishes/congratulations.json'):
        try:
            import json
            with open('wishes/congratulations.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ congratulations.json: {len(data)} поздравлений")
                else:
                    print("❌ wishes/congratulations.json: файл пустой или неверный формат")
                    all_ok = False
        except Exception as e:
            print(f"❌ wishes/congratulations.json: ошибка чтения - {e}")
            all_ok = False
    
    print("-" * 50)
    
    if all_ok:
        print("\n🎉 ВСЕ ФАЙЛЫ В ПОРЯДКЕ!")
        print("Запустите start_bot.bat для запуска бота")
    else:
        print("\n⚠️  ЕСТЬ ПРОБЛЕМЫ С ФАЙЛАМИ!")
        print("Исправьте их и запустите проверку снова")
    
    print("\n" + "=" * 50)
    
    # Ждем нажатия клавиши
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПроверка прервана пользователем")
        input("\nНажмите Enter для выхода...")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        input("\nНажмите Enter для выхода...")