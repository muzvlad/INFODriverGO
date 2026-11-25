@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 📥 Установка зависимостей

echo ========================================
echo 📥 УСТАНОВКА ЗАВИСИМОСТЕЙ
echo ========================================
echo.

echo 🔍 Проверка Python...
:: Проверяем доступность Python
:: Сначала пробуем py launcher с версией 3.11
py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=py -3.11
    goto :python_found
)
:: Затем обычный python (может быть 3.14)
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=python
    goto :python_found
)
:: Пробуем py launcher без указания версии
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=py
    goto :python_found
)
:: Python не найден
echo ❌ Python не найден!
echo Установите Python 3.11 или добавьте его в PATH
echo.
pause
exit /b 1

:python_found
echo ✅ Python найден!
!PYTHON_CMD! --version

echo.
echo 🐍 Версия Python: 
!PYTHON_CMD! -c "import sys; print('{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))"

echo.
echo 🧹 Удаление старых зависимостей...
:: Удаляем старые виртуальные окружения
if exist "venv" (
    echo Удаляю старое виртуальное окружение venv...
    rmdir /s /q venv
)
if exist "venv311_new" (
    echo Удаляю старое виртуальное окружение venv311_new...
    rmdir /s /q venv311_new
)

echo.
echo 🏗️ Создание нового виртуального окружения...
!PYTHON_CMD! -m venv venv
if errorlevel 1 (
    echo ❌ Ошибка создания виртуального окружения!
    pause
    exit /b 1
)

echo ✅ Виртуальное окружение создано

echo.
echo 📦 Установка зависимостей...
:: Обновляем pip
call venv\Scripts\python.exe -m pip install --upgrade pip --quiet

:: Устанавливаем зависимости из requirements.txt
call venv\Scripts\pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей!
    pause
    exit /b 1
)

echo.
echo ✅ Зависимости установлены!
echo 📊 Проверка установленных библиотек...

:: Проверяем установленные библиотеки
echo.
echo 📦 Установленные пакеты:
call venv\Scripts\pip list --disable-pip-version-check

echo.
echo 🔍 Проверка ключевых библиотек:
:: Создаем временный Python файл для проверки
echo import telegram > temp_check_deps.py
echo import dotenv >> temp_check_deps.py
echo import pytz >> temp_check_deps.py
echo print("^>^>^> Проверка установленных библиотек:") >> temp_check_deps.py
echo try: >> temp_check_deps.py
echo     import telegram >> temp_check_deps.py
echo     print("✅ python-telegram-bot:", telegram.__version__) >> temp_check_deps.py
echo except ImportError as e: >> temp_check_deps.py
echo     print("❌ python-telegram-bot: НЕ УСТАНОВЛЕН") >> temp_check_deps.py
echo try: >> temp_check_deps.py
echo     import dotenv >> temp_check_deps.py
echo     print("✅ python-dotenv: установлен") >> temp_check_deps.py
echo except ImportError as e: >> temp_check_deps.py
echo     print("❌ python-dotenv: НЕ УСТАНОВЛЕН") >> temp_check_deps.py
echo try: >> temp_check_deps.py
echo     import pytz >> temp_check_deps.py
echo     print("✅ pytz: установлен") >> temp_check_deps.py
echo except ImportError as e: >> temp_check_deps.py
echo     print("❌ pytz: НЕ УСТАНОВЛЕН") >> temp_check_deps.py


call venv\Scripts\python.exe temp_check_deps.py
del temp_check_deps.py 2>nul

echo.
echo ========================================
echo 📁 ПРОВЕРКА ФАЙЛОВ ПРОЕКТА:
echo ========================================
echo.

:: Проверяем обязательные файлы
set REQUIRED_FILES=0

if exist ".env" (
    echo ✅ .env найден
    set /a REQUIRED_FILES+=1
) else (
    echo ⚠️  .env не найден - создаю шаблон...
    echo BOT_TOKEN=ВАШ_ТОКЕН_БОТА > .env
    echo TIMEZONE=Europe/Moscow >> .env
    echo ⚠️  ЗАМЕНИТЕ ВАШ_ТОКЕН_БОТА на реальный токен!
)

:: Проверяем файлы в папке wishes
if exist "wishes\congratulations.json" (
    echo ✅ wishes\congratulations.json найден
    set /a REQUIRED_FILES+=1
) else (
    echo ❌ ОШИБКА: wishes\congratulations.json не найден!
    echo Этот файл ОБЯЗАТЕЛЕН для работы бота!
)

if exist "wishes\events.json" (
    echo ✅ wishes\events.json найден
    set /a REQUIRED_FILES+=1
) else (
    echo ⚠️  wishes\events.json не найден - создаю пустой файл...
    echo {"events": []} > wishes\events.json
)

if exist "wishes\weddings.json" (
    echo ✅ wishes\weddings.json найден
    set /a REQUIRED_FILES+=1
) else (
    echo ⚠️  wishes\weddings.json не найден - создаю пустой файл...
    echo {"weddings": []} > wishes\weddings.json
)

if exist "config.py" (
    echo ✅ config.py найден
    set /a REQUIRED_FILES+=1
) else (
    echo ❌ ОШИБКА: config.py не найден!
)

if exist "requirements.txt" (
    echo ✅ requirements.txt найден
    set /a REQUIRED_FILES+=1
) else (
    echo ❌ ОШИБКА: requirements.txt не найден!
)

echo.
echo 📊 Найдено %REQUIRED_FILES% из 6 обязательных файлов (.env, config.py, requirements.txt и 3 файла из папки wishes)

echo.
echo ========================================
echo 🎉 УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo 💡 Для запуска бота используйте start_bot.bat
echo.
pause
exit /b 0

:error
echo.
echo ❌ Произошла ошибка при установке зависимостей
pause
exit /b 1