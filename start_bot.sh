#!/bin/bash

# Функция для отображения меню
show_menu() {
    clear
    echo "========================================"
    echo "ЗАПУСК TELEGRAM БОТА ДЛЯ ДНЕЙ РОЖДЕНИЯ"
    echo "========================================"
    echo ""
    
    echo "1. Проверка файлов"
    echo "2. Запустить бота"
    echo "3. Проверить токен бота"
    echo "4. Установка зависимостей и библиотек"
    echo "5. Посмотреть логи бота"
    echo "6. Остановить бота"
    echo "7. Выйти"
    echo ""
    echo -n "Выберите действие (1-7): "
}

# Функция для запуска бота
run_bot() {
    clear
    echo "========================================"
    echo "ЗАПУСК БОТА"
    echo "========================================"
    echo ""
    
    echo "[INFO] Проверка и завершение предыдущих процессов бота..."
    # Завершаем предыдущие процессы бота
    pkill -f "python.*main.py" 2>/dev/null
    
    echo "[OK] Предыдущие процессы завершены (если были)"
    echo ""
    
    echo "[INFO] Активация виртуального окружения..."
    # Активируем виртуальное окружение
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "[OK] Виртуальное окружение активировано"
    else
        echo "[ERROR] Виртуальное окружение venv не найдено!"
        echo "Создайте его командой: python3 -m venv venv"
        echo "Затем установите зависимости: ./install_dependencies.sh"
        echo ""
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    echo ""
    
    echo "Проверка зависимостей..."
    python -c "import telegram, dotenv, pytz" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Не все зависимости установлены!"
        echo "Запустите: ./install_dependencies.sh"
        echo ""
        read -p "Нажмите Enter для продолжения..."
        return
    fi
    
    echo "[OK] Зависимости установлены"
    echo ""
    echo "Бот запускается..."
    echo "Для остановки нажмите Ctrl+C"
    echo ""
    echo "Логи бота:"
    echo "=========="
    echo ""
    
    # Запускаем бота
    python main.py
    
    echo ""
    echo "========================================"
    echo "БОТ ОСТАНОВЛЕН"
    echo "========================================"
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Функция проверки файлов
check_files() {
    clear
    echo "========================================"
    echo "ПРОВЕРКА ФАЙЛОВ"
    echo "========================================"
    echo ""
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if [ -f "check_files.py" ]; then
            python check_files.py
        else
            echo "Файл check_files.py не найден"
        fi
    else
        echo "Виртуальное окружение не найдено"
    fi
    
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Функция проверки токена
check_token() {
    clear
    echo "========================================"
    echo "ПРОВЕРКА ТОКЕНА БОТА"
    echo "========================================"
    echo ""
    
    if [ -f ".env" ]; then
        echo "Содержимое файла .env:"
        echo "---------------------"
        cat .env
        echo ""
    else
        echo "Файл .env не найден"
    fi
    
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Функция установки зависимостей
install_deps() {
    clear
    echo "========================================"
    echo "УСТАНОВКА ЗАВИСИМОСТЕЙ"
    echo "========================================"
    echo ""
    
    if [ -f "install_dependencies.sh" ]; then
        ./install_dependencies.sh
    else
        echo "Файл install_dependencies.sh не найден"
    fi
    
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Функция просмотра логов
view_logs() {
    clear
    echo "========================================"
    echo "ЛОГИ БОТА"
    echo "========================================"
    echo ""
    
    echo "Последние 30 строк лога (если бот запущен через systemd):"
    if systemctl is-active --quiet telegram-bot.service 2>/dev/null; then
        sudo journalctl -u telegram-bot.service -n 30 --no-pager
    else
        echo "Бот не запущен как systemd-сервис"
        echo ""
        echo "Процессы Python:"
        ps aux | grep -E "python.*main.py" | grep -v grep
        
        echo ""
        echo "Последние строки из лога (если есть):"
        if [ -f "nohup.out" ]; then
            tail -30 nohup.out
        fi
    fi
    
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Функция остановки бота
stop_bot() {
    clear
    echo "========================================"
    echo "ОСТАНОВКА БОТА"
    echo "========================================"
    echo ""
    
    if systemctl is-active --quiet telegram-bot.service 2>/dev/null; then
        echo "Останавливаю systemd-сервис..."
        sudo systemctl stop telegram-bot.service
        echo "✅ Бот остановлен"
    else
        echo "Ищу процессы бота..."
        pids=$(pgrep -f "python.*main.py")
        if [ -n "$pids" ]; then
            echo "Найдены процессы: $pids"
            kill $pids 2>/dev/null
            sleep 2
            # Проверяем, не зависли ли
            pids=$(pgrep -f "python.*main.py")
            if [ -n "$pids" ]; then
                echo "Процессы не отвечают, принудительное завершение..."
                kill -9 $pids 2>/dev/null
            fi
            echo "✅ Бот остановлен"
        else
            echo "Процессы бота не найдены"
        fi
    fi
    
    echo ""
    read -p "Нажмите Enter для возврата в меню..."
}

# Основной цикл меню
while true; do
    show_menu
    read choice
    
    case $choice in
        1) check_files ;;
        2) run_bot ;;
        3) check_token ;;
        4) install_deps ;;
        5) view_logs ;;
        6) stop_bot ;;
        7) 
            echo ""
            echo "До свидания!"
            exit 0
            ;;
        *)
            echo ""
            echo "Неправильный выбор"
            sleep 1
            ;;
    esac
done