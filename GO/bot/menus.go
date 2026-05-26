package bot

import (
	"fmt"
	"strconv"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func (b *Bot) sendMainMenu(chatID int64, messageID int) {
	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("🎂 Дни рождения", "bd_menu"),
			tgbotapi.NewInlineKeyboardButtonData("💍 Свадьбы", "wed_menu"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("📅 События", "events_menu"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("⚙️ Настройки", "show_settings"),
		),
	)

	msg := tgbotapi.NewEditMessageText(chatID, messageID, "🎂 *Меню управления ботом*\n\nВыберите действие:")
	msg.ParseMode = "Markdown"
	keyboard.InlineKeyboard = append(keyboard.InlineKeyboard,
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("✅ Включить", "enable_notifications"),
			tgbotapi.NewInlineKeyboardButtonData("❌ Выключить", "disable_notifications"),
		),
	)
	msg.ReplyMarkup = &keyboard
	b.api.Send(msg)
}

func (b *Bot) sendSettingsWithKeyboard(chatID string, chat *tgbotapi.Chat) {
	settings := b.db.GetGroupSettings(chatID)
	stats := b.db.GetStatistics()
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	weddings := b.db.GetWeddingsForGroup(chatID)
	events := b.db.GetEventsForGroup(chatID)

	notifications := "❌ Выключены"
	if settings.NotificationsEnabled {
		notifications = "✅ Включены"
	}

	text := fmt.Sprintf(`⚙️ *Настройки уведомлений:*

🔔 Статус: %s
⏰ Время: %s

📊 *Статистика:*
• Дней рождения: %d
• Свадеб: %d
• Событий: %d
• Всего групп: %d

👑 Администратор: @%s`,
		notifications, settings.NotificationTime,
		len(birthdays), len(weddings), len(events), stats["total_groups"],
		b.cfg.AdminUsername)

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("09:00", "set_time_09:00"),
			tgbotapi.NewInlineKeyboardButtonData("10:00", "set_time_10:00"),
			tgbotapi.NewInlineKeyboardButtonData("12:00", "set_time_12:00"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("18:00", "set_time_18:00"),
			tgbotapi.NewInlineKeyboardButtonData("19:00", "set_time_19:00"),
			tgbotapi.NewInlineKeyboardButtonData("20:00", "set_time_20:00"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("✅ Включить", "enable_notifications"),
			tgbotapi.NewInlineKeyboardButtonData("❌ Выключить", "disable_notifications"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "back_to_main"),
		),
	)

	msg := tgbotapi.NewMessage(chat.ID, text)
	msg.ParseMode = "Markdown"
	msg.ReplyMarkup = &keyboard
	b.api.Send(msg)
}

func (b *Bot) handleBirthdayMenu(chatID string) string {
	msg := "🎂 *Дни рождения*\n\nВыберите действие:"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("➕ Добавить", "bd_add"),
			tgbotapi.NewInlineKeyboardButtonData("📋 Список", "bd_list"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("🗑️ Удалить", "bd_delete"),
			tgbotapi.NewInlineKeyboardButtonData("📅 Сегодня", "bd_today"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("⏰ Ближайшие", "bd_upcoming"),
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "main_menu"),
		),
	)

	chatIDInt, _ := strconv.ParseInt(chatID, 10, 64)
	b.sendMenu(chatIDInt, msg, &keyboard)
	return ""
}

func (b *Bot) handleWeddingsMenu(chatID string) string {
	msg := "💍 *Годовщины свадеб*\n\nВыберите действие:"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("➕ Добавить", "wed_add"),
			tgbotapi.NewInlineKeyboardButtonData("📋 Список", "wed_list"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("🗑️ Удалить", "wed_delete"),
			tgbotapi.NewInlineKeyboardButtonData("📅 Сегодня", "wed_today"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "main_menu"),
		),
	)

	chatIDInt, _ := strconv.ParseInt(chatID, 10, 64)
	b.sendMenu(chatIDInt, msg, &keyboard)
	return ""
}

func (b *Bot) handleEventsMenu(chatID string) string {
	msg := "📅 *События*\n\nВыберите действие:"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("➕ Добавить", "evt_add"),
			tgbotapi.NewInlineKeyboardButtonData("📋 Список", "evt_list"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("🗑️ Удалить", "evt_delete"),
			tgbotapi.NewInlineKeyboardButtonData("ℹ️ Типы", "evt_types"),
		),
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "main_menu"),
		),
	)

	chatIDInt, _ := strconv.ParseInt(chatID, 10, 64)
	b.sendMenu(chatIDInt, msg, &keyboard)
	return ""
}

func (b *Bot) sendMenu(chatID int64, text string, keyboard *tgbotapi.InlineKeyboardMarkup) {
	msg := tgbotapi.NewMessage(chatID, text)
	msg.ParseMode = "Markdown"
	msg.ReplyMarkup = keyboard
	b.api.Send(msg)
}