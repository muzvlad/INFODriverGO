package bot

import (
	"fmt"
	"os"
	"path/filepath"
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
	allGroups := b.db.GetAllGroups()

	totalBirthdays := 0
	totalWeddings := 0
	totalEvents := 0

	for _, settings := range allGroups {
		birthdays := b.db.GetBirthdaysForGroup(settings.ChatID)
		weddings := b.db.GetWeddingsForGroup(settings.ChatID)
		events := b.db.GetEventsForGroup(settings.ChatID)
		totalBirthdays += len(birthdays)
		totalWeddings += len(weddings)
		totalEvents += len(events)
	}

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
		totalBirthdays, totalWeddings, totalEvents,
		len(b.congratulations))
}

func (b *Bot) handleAdminFiles() string {
	groupsDir := "groups"

	entries, err := os.ReadDir(groupsDir)
	if err != nil {
		return "❌ Директория groups не найдена."
	}

	jsonFiles := 0
	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".json") {
			jsonFiles++
		}
	}

	result := fmt.Sprintf("📁 *Информация о файлах:*\n\n📂 Директория: %s\n📄 JSON файлов: %d\n\n📝 *Список файлов:*\n", groupsDir, jsonFiles)

	count := 0
	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".json") && count < 10 {
			path := filepath.Join(groupsDir, entry.Name())
			info, _ := os.Stat(path)
			if info != nil {
				result += fmt.Sprintf("• %s (%d bytes)\n", entry.Name(), info.Size())
			}
			count++
		}
	}

	if jsonFiles > 10 {
		result += fmt.Sprintf("... и еще %d файлов", jsonFiles-10)
	}

	return result
}