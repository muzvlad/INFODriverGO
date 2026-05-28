package bot

import (
	"fmt"
	"os"
	"strings"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func (b *Bot) handleAdmin(chatID string, user *tgbotapi.User, args string) string {
	if user == nil || user.UserName != b.cfg.AdminUsername {
		return "❌ Эта команда доступна только администратору!"
	}

	parts := strings.SplitN(strings.TrimSpace(args), " ", 2)
	subcommand := ""
	if len(parts) > 0 {
		subcommand = strings.ToLower(parts[0])
	}

	switch subcommand {
	case "список", "list":
		return b.handleAdminList()
	case "статистика", "stats":
		return b.handleAdminStats()
	case "файлы", "files":
		return b.handleAdminFiles()
	default:
		return b.handleAdminMain()
	}
}

func (b *Bot) handleAdminMain() string {
	stats := b.db.GetStatistics()

	return fmt.Sprintf(`👑 *АДМИНИСТРАТИВНАЯ ПАНЕЛЬ*

📊 *Статистика:*
• Всего групп: %d
• С уведомлениями: %d
• Без уведомлений: %d
• Поздравлений в базе: %d

📝 *Команды администратора:*
• /админ список - список всех групп
• /админ статистика - подробная статистика
• /админ файлы - информация о файлах`,
		stats["total_groups"], stats["groups_with_notifications"], stats["groups_without_notifications"],
		len(b.congratulations))
}

func (b *Bot) handleAdminList() string {
	allGroups := b.db.GetAllGroups()

	if len(allGroups) == 0 {
		return "❌ Нет зарегистрированных групп."
	}

	result := "📋 *Список всех групп:*\n\n"

	for _, settings := range allGroups {
		status := "🔕 Выкл"
		if settings.NotificationsEnabled {
			status = "🔔 Вкл"
		}
		result += fmt.Sprintf("• %s (ID: %s)\n  Статус: %s, Время: %s\n\n",
			settings.ChatName, settings.ChatID, status, settings.NotificationTime)
	}

	return result
}

func (b *Bot) handleAdminStats() string {
	stats := b.db.GetStatistics()
	totals := b.db.GetAllTotals()

	return fmt.Sprintf(`📊 *Подробная статистика:*

👥 *Группы:*
• Всего групп: %d
• С уведомлениями: %d
• Без уведомлений: %d

🎂 *Дни рождения:*
• Всего записей: %d

💍 *Свадьбы:*
• Всего записей: %d

📅 *События:*
• Всего записей: %d

🎉 *Поздравления:*
• В базе: %d шт.`,
		stats["total_groups"], stats["groups_with_notifications"], stats["groups_without_notifications"],
		totals["total_birthdays"], totals["total_weddings"], totals["total_events"],
		len(b.congratulations))
}

func (b *Bot) handleAdminFiles() string {
	dbPath := "bot.db"
	info, err := os.Stat(dbPath)
	size := "N/A"
	if err == nil {
		size = fmt.Sprintf("%d bytes", info.Size())
	}

	return fmt.Sprintf("📁 *Информация о БД:*\n\n🗄️ Файл: %s\n📏 Размер: %s\n\n✅ Все данные хранятся в SQLite.", dbPath, size)
}