#!/bin/bash

echo "========================================"
echo "📥 УСТАНОВКА ЗАВИСИМОСТЕЙ"
echo "========================================"
echo ""

echo "🔍 Проверка Python..."

# Проверяем наличие Python 3.11+
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Найден Python 3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "✅ Найден Python ${PYTHON_VERSION}"
    
    # Проверяем версию (должна быть 3.11+)
    if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
        echo "❌ Требуется Python 3.11 или выше, у вас ${PYTHON_VERSION}"
        echo "Установите Python 3.11: sudo apt install python3.11"
        exit 1
    fi
else
    echo "❌ Python не найден!"
    echo "Установите Python 3.11: sudo apt install python3.11"
    exit 1
fi

echo ""
echo "🐍 Версия Python:"
$PYTHON_CMD --version

echo ""
echo "🧹 Удаление старых зависимостей..."
# Удаляем старое виртуальное окружение
if [ -d "venv" ]; then
    echo "Удаляю старое виртуальное окружение venv..."
    rm -rf venv
fi

echo ""
echo "🏗️ Создание нового виртуального окружения..."
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Ошибка создания виртуального окружения!"
    echo "Установите python3-venv: sudo apt install python3-venv"
    exit 1
fi

echo "✅ Виртуальное окружение создано"

echo ""
echo "📦 Установка зависимостей..."
# Обновляем pip
venv/bin/python -m pip install --upgrade pip --quiet

# Устанавливаем зависимости из requirements.txt
venv/bin/pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей!"
    exit 1
fi

echo ""
echo "✅ Зависимости установлены!"
echo "📊 Проверка установленных библиотек..."
echo ""

# Показываем установленные пакеты
echo "📦 Установленные пакеты:"
venv/bin/pip list

echo ""
echo "🔍 Проверка ключевых библиотек:"
# Создаем временный Python файл для проверки
cat > temp_check_deps.py << 'EOF'
import sys
print(">>> Проверка установленных библиотек:")
try:
    import telegram
    print(f"✅ python-telegram-bot: {telegram.__version__}")
except ImportError as e:
    print("❌ python-telegram-bot: НЕ УСТАНОВЛЕН")
try:
    import dotenv
    print("✅ python-dotenv: установлен")
except ImportError as e:
    print("❌ python-dotenv: НЕ УСТАНОВЛЕН")
try:
    import pytz
    print("✅ pytz: установлен")
except ImportError as e:
    print("❌ pytz: НЕ УСТАНОВЛЕН")
EOF

venv/bin/python temp_check_deps.py
rm temp_check_deps.py 2>/dev/null

echo ""
echo "========================================"
echo "📁 ПРОВЕРКА ФАЙЛОВ ПРОЕКТА:"
echo "========================================"
echo ""

# Проверяем обязательные файлы
REQUIRED_FILES=0

if [ -f ".env" ]; then
    echo "✅ .env найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "⚠️  .env не найден - создаю шаблон..."
    echo "BOT_TOKEN=ВАШ_ТОКЕН_БОТА" > .env
    echo "TIMEZONE=Europe/Moscow" >> .env
    echo "⚠️  ЗАМЕНИТЕ ВАШ_ТОКЕН_БОТА на реальный токен!"
fi

# Проверяем файлы в папке wishes
if [ -f "wishes/congratulations.json" ]; then
    echo "✅ wishes/congratulations.json найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "❌ ОШИБКА: wishes/congratulations.json не найден!"
    echo "Этот файл ОБЯЗАТЕЛЕН для работы бота!"
fi

if [ -f "wishes/events.json" ]; then
    echo "✅ wishes/events.json найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "⚠️  wishes/events.json не найден - создаю пустой файл..."
    mkdir -p wishes
    echo '{"events": []}' > wishes/events.json
fi

if [ -f "wishes/weddings.json" ]; then
    echo "✅ wishes/weddings.json найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "⚠️  wishes/weddings.json не найден - создаю пустой файл..."
    mkdir -p wishes
    echo '{"weddings": []}' > wishes/weddings.json
fi

if [ -f "config.py" ]; then
    echo "✅ config.py найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "❌ ОШИБКА: config.py не найден!"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt найден"
    REQUIRED_FILES=$((REQUIRED_FILES + 1))
else
    echo "❌ ОШИБКА: requirements.txt не найден!"
fi

echo ""
echo "📊 Найдено ${REQUIRED_FILES} из 6 обязательных файлов"

echo ""
echo "========================================"
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "========================================"
echo ""
echo "💡 Для запуска бота используйте: ./start_bot.sh"
echo ""