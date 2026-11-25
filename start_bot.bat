@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

title Birthday Bot - Запуск
:: Убрано ограничение строк для полного отображения логов
:: mode con: cols=80 lines=40
color 0E

:: Проверяем доступность Python
title Проверка Python...
echo [DEBUG] Проверяем py -3.11...
py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD="py -3.11"
    echo [INFO] Найден Python 3.11 через py launcher
    goto :python_found
)

echo [DEBUG] Проверяем python...
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=python
    echo [INFO] Найден Python через команду python
    goto :python_found
)

echo [DEBUG] Проверяем py...
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=py
    echo [INFO] Найден Python через py launcher
    goto :python_found
)

echo [ERROR] Python не найден!
echo Установите Python 3.11 или добавьте его в PATH
echo.
pause
exit /b 1

:python_found
echo [INFO] Используется команда Python: !PYTHON_CMD!
:: Убираем кавычки для корректного использования
set PYTHON_CMD_NO_QUOTES=!PYTHON_CMD:"=!

title Birthday Bot - Запуск

:: Пропускаем меню и сразу запускаем бота
echo [INFO] Проверка и завершение предыдущих процессов бота...
:: Завершаем предыдущие процессы Python, связанные с ботом
taskkill /f /im python.exe /fi "WINDOWTITLE eq Birthday Bot*" 2>nul
taskkill /f /im py.exe /fi "WINDOWTITLE eq Birthday Bot*" 2>nul

echo [OK] Предыдущие процессы завершены (если были)
echo.

echo [INFO] Активация виртуального окружения Python 3.11...
:: Активируем виртуальное окружение
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Виртуальное окружение активировано
) else (
    echo [WARNING] Виртуальное окружение venv не найдено
    echo Создайте его командой: python -m venv venv
    echo Затем установите зависимости: venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo.

echo Проверка зависимостей...
venv\Scripts\python.exe -c "import telegram, dotenv, pytz" 2>nul
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Не все зависимости установлены!
    echo Запустите: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Зависимости установлены
echo.
echo Бот запускается...
echo Для остановки нажмите Ctrl+C
echo.
echo Логи бота:
echo ==========
echo.

:: Устанавливаем заголовок окна для идентификации
:: Запускаем бота
title Birthday Bot - Работает (%date% %time%)
venv\Scripts\python.exe main.py

echo.
echo ========================================
echo БОТ ОСТАНОВЛЕН
echo ========================================
echo.
pause
goto :menu

:menu
cls
echo ========================================
echo ЗАПУСК TELEGRAM БОТА ДЛЯ ДНЕЙ РОЖДЕНИЯ
echo ========================================
echo.

echo 1. Проверка файлов
echo 2. Запустить бота
echo 3. Проверить токен бота
echo 4. Установка зависимостей и библиотек
echo 5. Выйти
echo.
set /p choice="Выберите действие (1-5): "

if "%choice%"=="1" goto :check_files
if "%choice%"=="2" goto :run_bot
if "%choice%"=="3" goto :check_token
if "%choice%"=="4" goto :install_deps
if "%choice%"=="5" exit /b

echo Неправильный выбор
timeout /t 2 >nul
goto :menu

:check_files
cls
echo ========================================
echo ПРОВЕРКА ФАЙЛОВ
echo ========================================
echo.
venv\Scripts\python.exe check_files.py
echo.
pause
goto :menu

:check_token
cls
echo ========================================
echo ПРОВЕРКА ТОКЕНА БОТА
echo ========================================
echo.
if exist ".env" (
    echo Содержимое файла .env:
    echo ---------------------
    type .env
    echo.
) else (
    echo Файл .env не найден
)
echo.
pause
goto :menu

:run_bot
cls
echo ========================================
echo ЗАПУСК БОТА
echo ========================================
echo.

echo [INFO] Проверка и завершение предыдущих процессов бота...
:: Завершаем предыдущие процессы Python, связанные с ботом
taskkill /f /im python.exe /fi "WINDOWTITLE eq Birthday Bot*" 2>nul
taskkill /f /im py.exe /fi "WINDOWTITLE eq Birthday Bot*" 2>nul

echo [OK] Предыдущие процессы завершены (если были)
echo.

echo [INFO] Активация виртуального окружения Python 3.11...
:: Активируем виртуальное окружение
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Виртуальное окружение активировано
) else (
    echo [WARNING] Виртуальное окружение venv не найдено
    echo Создайте его командой: python -m venv venv
    echo Затем установите зависимости: venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    goto :menu
)
echo.

echo Проверка зависимостей...
venv\Scripts\python.exe -c "import telegram, dotenv, pytz" 2>nul
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Не все зависимости установлены!
    echo Запустите: pip install -r requirements.txt
    echo.
    pause
    goto :menu
)

echo [OK] Зависимости установлены
echo.
echo Бот запускается...
echo Для остановки нажмите Ctrl+C
echo.
echo Логи бота:
echo ==========
echo.

:: Устанавливаем заголовок окна для идентификации
:: Запускаем бота
title Birthday Bot - Работает (%date% %time%)
venv\Scripts\python.exe main.py

echo.
echo ========================================
echo БОТ ОСТАНОВЛЕН
echo ========================================
echo.
pause
goto :menu
:install_deps
cls
echo ========================================
echo ��������� ������������ � ���������
echo ========================================
echo.
call install_dependencies.bat
echo.
pause
goto :menu

