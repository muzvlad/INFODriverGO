"""Модуль для запуска бота"""
import logging
import asyncio
import sys
import os

# Патчим ssl до импорта telegram для отключения проверки сертификатов
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.request import HTTPXRequest
import httpx

from config import config


class SSLDisabledHTTPXRequest(HTTPXRequest):
    """Кастомный HTTPXRequest с отключенной проверкой SSL"""
    
    def _create_client(self) -> httpx.Client:
        return httpx.Client(
            verify=False,
            timeout=httpx.Timeout(30.0, connect=10.0)
        )


logger = logging.getLogger(__name__)


class BotRunner:
    """Класс для запуска бота"""
    
    def __init__(self, main_bot):
        self.bot = main_bot
    
    def run(self):
        """Запускает бота"""
        try:
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            
            # Проверяем версию Python
            if sys.version_info >= (3, 14):
                print(f"⚠️  ВНИМАНИЕ: Обнаружена Python {python_version}")
                print("⚠️  Возможны проблемы совместимости с python-telegram-bot")
                print("⚠️  Рекомендуется использовать Python 3.11 или более раннюю версию")
                print()
            else:
                print(f"✅ Используется Python {python_version} - совместимость обеспечена")
                print()
            
            # Создаем приложение с отключенным JobQueue для Python 3.14+
            from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
            
            # Для Python 3.14+ создаем event loop вручную
            if sys.version_info >= (3, 14):
                try:
                    # Проверяем, есть ли уже event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # Если нет, создаем новый
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    print("🔄 Event loop готов для Python 3.14+")
                except Exception as e:
                    print(f"⚠️ Ошибка настройки event loop: {e}")
            
            # Создаем приложение с улучшенными сетевыми настройками
            # Используем кастомный класс с отключенной SSL верификацией
            
            # Настраиваем HTTP запросы с увеличенными таймаутами и размером пула соединений
            request = SSLDisabledHTTPXRequest(
                connection_pool_size=10,
                read_timeout=20.0,
                write_timeout=20.0,
                connect_timeout=10.0,
                pool_timeout=5.0,
                http_version="1.1"
            )
            
            # Настраиваем отдельные параметры для get_updates
            get_updates_request = SSLDisabledHTTPXRequest(
                connection_pool_size=5,
                read_timeout=30.0,
                write_timeout=20.0,
                connect_timeout=10.0,
                pool_timeout=5.0,
                http_version="1.1"
            )
            
            self.bot.application = (
                Application.builder()
                .token(config.BOT_TOKEN)
                .request(request)
                .get_updates_request(get_updates_request)
                .build()
            )
            
            # Добавляем ссылку на бота в контекст приложения
            self.bot.application.main_bot = self.bot
            
            # Явно запускаем JobQueue если он есть
            if self.bot.application.job_queue:
                print("✅ JobQueue доступен и будет запущен автоматически")
            else:
                print("⚠️ JobQueue недоступен")
            
            # Регистрируем обработчики команд
            # Английские команды
            self.bot.application.add_handler(CommandHandler("start", self.bot.start_command))
            self.bot.application.add_handler(CommandHandler("help", self.bot.help_command))
            
            # Русские команды через MessageHandler
            russian_commands_handler = MessageHandler(
                filters.TEXT & (
                    filters.Regex(r'^/старт') |
                    filters.Regex(r'^/справка') |
                    filters.Regex(r'^/настройки') |
                    filters.Regex(r'^/добавить') |
                    filters.Regex(r'^/список') |
                    filters.Regex(r'^/удалить') |
                    filters.Regex(r'^/сегодня') |
                    filters.Regex(r'^/ближайшие') |
                    filters.Regex(r'^/включить') |
                    filters.Regex(r'^/выключить') |
                    filters.Regex(r'^/статус') |
                    filters.Regex(r'^/время') |
                    filters.Regex(r'^/админ') |
                    # Свадебные команды
                    filters.Regex(r'^/свадьба') |
                    filters.Regex(r'^/свадьбы') |
                    filters.Regex(r'^/несвадьба') |
                    # Событийные команды
                    filters.Regex(r'^/событие') |
                    filters.Regex(r'^/события') |
                    filters.Regex(r'^/несобытие')
                ),
                self.bot.handle_russian_command
            )
            self.bot.application.add_handler(russian_commands_handler)
            
            # Обработчик кнопок
            self.bot.application.add_handler(CallbackQueryHandler(self.bot.button_callback))
            
            # Добавляем обработчики ошибок
            async def error_handler(update, context):
                """Обработчик ошибок ассистента"""
                logger.error(f"Ошибка в обработке обновления: {context.error}")
                
                # Отправляем сообщение пользователю
                if update and update.effective_message:
                    try:
                        await update.effective_message.reply_text(
                            "❌ Произошла ошибка при обработке команды. Попробуйте повторить позже."
                        )
                    except:
                        pass
            
            self.bot.application.add_error_handler(error_handler)
            
            # Инициализируем планировщик для всех групп с включенными уведомлениями
            if self.bot.application.job_queue:
                print("🔄 Запуск JobQueue...")
                # Принудительно запускаем JobQueue
                try:
                    # Проверяем состояние JobQueue
                    job_queue_status = "активен" if self.bot.application.job_queue.scheduler.running else "не активен"
                    print(f"📊 Состояние JobQueue: {job_queue_status}")
                    
                    # JobQueue должен запускаться автоматически при запуске Application
                    # Но на всякий случай проверим его состояние
                    # JobQueue готов к работе
                    # Мониторинг JobQueue отключен для стабильности
                        
                except Exception as e:
                    print(f"❌ Ошибка при подготовке JobQueue: {e}")
                
                groups = self.bot.settings_manager.get_all_groups()
                for chat_id, group_data in groups.items():
                    if group_data.get("notifications_enabled", False):
                        try:
                            # Настраиваем основные уведомления о днях рождения
                            self.bot.job_scheduler.setup_group_job(
                                chat_id, 
                                self.bot.settings_manager, 
                                self.bot.application.job_queue
                            )
                            
                            # Настраиваем события
                            self.bot.job_scheduler.setup_event_jobs(
                                chat_id,
                                self.bot.settings_manager,
                                self.bot.application.job_queue,
                                self.bot.job_scheduler.timezone,
                                self.bot
                            )
                            
                            # Настраиваем свадьбы
                            self.bot.job_scheduler.setup_wedding_jobs(
                                chat_id,
                                self.bot.settings_manager,
                                self.bot.application.job_queue
                            )
                            
                        except Exception as e:
                            print(f"❌ Ошибка настройки планировщика для группы {chat_id}: {e}")
                            logger.error(f"Ошибка настройки планировщика для группы {chat_id}: {e}")
            else:
                print("⚠️ JobQueue недоступен - планировщик не будет работать")
            
            # Бот инициализирован
            # JobQueue запускается автоматически с Application
            
            # Запускаем polling
            print("\n🚀 Ассистент запущен и ожидает команды...")
            print("Для остановки нажмите Ctrl+C\n")
            
            try:
                self.bot.application.run_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query"],
                    poll_interval=15,  # Увеличиваем интервал до 15 секунд для снижения нагрузки
                    timeout=45,        # Увеличиваем таймаут до 45 секунд
                    bootstrap_retries=3,  # Добавляем повторные попытки при ошибках
                    read_timeout=30.0,    # Увеличиваем таймауты для сетевых операций
                    write_timeout=30.0,
                    connect_timeout=15.0
                )
                print("✅ Polling завершен")
            except KeyboardInterrupt:
                print("\n🛑 Ассистент остановлен пользователем")
            except Exception as e:
                # Улучшенная обработка сетевых ошибок
                error_msg = str(e)
                if "httpx.ReadError" in error_msg or "Connection" in error_msg or "timeout" in error_msg.lower():
                    print(f"⚠️ Сетевая ошибка: {error_msg}")
                    print("💡 Проверьте интернет-соединение и повторите попытку")
                else:
                    print(f"❌ Ошибка в polling: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            print(f"❌ Ошибка запуска ассистента: {e}")