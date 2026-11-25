"""Класс CommandHandlers - объединяет все модули команд"""
from .user_commands import UserCommands
from .admin_commands import AdminCommands
from .birthday_commands import BirthdayCommands
from .wedding_commands import WeddingCommands
from .event_commands import EventCommands
from .status_handlers import StatusHandlers


class CommandHandlers:
    """Основной класс обработчиков команд, объединяющий все модули"""
    
    def __init__(self, bot):
        self.bot = bot
        # Инициализируем все модули
        self.user_commands = UserCommands(bot)
        self.admin_commands = AdminCommands(bot)
        self.birthday_commands = BirthdayCommands(bot)
        self.wedding_commands = WeddingCommands(bot)
        self.event_commands = EventCommands(bot)
        self.status_handlers = StatusHandlers(bot)
    
    # Методы пользовательских команд
    async def start_command(self, update, context):
        return await self.user_commands.start_command(update, context)
    
    async def help_command(self, update, context):
        return await self.user_commands.help_command(update, context)
    
    async def settings_command(self, update, context):
        return await self.user_commands.settings_command(update, context)
    
    async def enable_notifications(self, update, context):
        return await self.user_commands.enable_notifications(update, context)
    
    async def disable_notifications(self, update, context):
        return await self.user_commands.disable_notifications(update, context)
    
    async def set_notification_time(self, update, context):
        return await self.user_commands.set_notification_time(update, context)
    
    # Методы административных команд
    async def admin_command(self, update, context):
        return await self.admin_commands.admin_command(update, context)
    
    # Методы работы с днями рождения
    async def add_birthday(self, update, context):
        return await self.birthday_commands.add_birthday_command(update, context)
    
    async def list_birthdays(self, update, context):
        return await self.birthday_commands.list_birthdays_command(update, context)
    
    async def delete_birthday(self, update, context):
        return await self.birthday_commands.delete_birthday_command(update, context)
    
    async def today_birthdays(self, update, context):
        return await self.birthday_commands.today_birthdays_command(update, context)
    
    async def upcoming_birthdays(self, update, context):
        return await self.birthday_commands.upcoming_birthdays_command(update, context)
    
    # Методы работы со свадьбами
    async def add_wedding(self, update, context):
        return await self.wedding_commands.add_wedding_command(update, context)
    
    async def list_weddings(self, update, context):
        return await self.wedding_commands.list_weddings_command(update, context)
    
    async def delete_wedding(self, update, context):
        return await self.wedding_commands.delete_wedding_command(update, context)
    
    # Методы работы с событиями
    async def add_event(self, update, context):
        return await self.event_commands.add_event_command(update, context)
    
    async def list_events(self, update, context):
        return await self.event_commands.list_events_command(update, context)
    
    async def delete_event(self, update, context):
        return await self.event_commands.delete_event_command(update, context)
    
    # Методы статуса
    async def status_command(self, update, context):
        return await self.status_handlers.status_command(update, context)
    
    async def handle_russian_command(self, update, context):
        return await self.status_handlers.handle_russian_command(update, context)