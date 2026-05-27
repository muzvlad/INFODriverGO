package bot

import (
	"fmt"
	"strconv"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func (b *Bot) handleStart(chatID string, user *tgbotapi.User) string {
	settings := b.db.GetGroupSettings(chatID)

	notifications := "❌ Выключены"
	if settings.NotificationsEnabled {
		notifications = "✅ Включены"
	}

	return fmt.Sprintf(`🎉 *Добро пожаловать в Ассистента дней рождения!*

Я помогу вам не забывать о важных датах ваших друзей и коллег.

📋 *Что я умею:*
• Добавлять и удалять дни рождения
• Добавлять и удалять годовщины свадеб 💍
• Добавлять события: ежедневные, еженедельные, ежемесячные и одноразовые 📅
• Показывать именинников сегодня и в ближайшие дни
• Отправлять автоматические поздравления и напоминания
• Работать отдельно в каждой группе

⚙️ *Текущие настройки:*
• Уведомления: %s
• Время уведомлений: %s

👑 Администратор: @%s

Используйте /справка для списка команд.`, notifications, settings.NotificationTime, b.cfg.AdminUsername)
}

func (b *Bot) handleHelp() string {
	return `🎂 *СПРАВКА ПО КОМАНДАМ*

📅 *ДНИ РОЖДЕНИЯ*
/рождение - меню управления (кнопки)
Добавить: /добавить Иван 15.03
Список: /список
Удалить: /удалить Иван
Сегодня: /сегодня
Ближайшие: /ближайшие

💍 *ГОДОВЩИНЫ СВАДЕБ*
/свадьбы - меню управления (кнопки)
Добавить: /свадьба Мария 22.07

📅 *СОБЫТИЯ*
/события - меню управления (кнопки)
Добавить: /событие ежедневно 09:00 утро
Добавить: /событие еженедельно суббота 20:00 кино
Добавить: /событие ежемесячно 15 10:00 зарплата
Добавить: /событие одноразово 25.12.2026 12:00 встреча

🔔 *УПРАВЛЕНИЕ*
/включить - включить уведомления
/выключить - выключить уведомления
/время ЧЧ:ММ - изменить время
/настройки - настройки с кнопками`
}

func (b *Bot) handleSettings(chatID string, chat *tgbotapi.Chat) string {
	settings := b.db.GetGroupSettings(chatID)
	stats := b.db.GetStatistics()
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	weddings := b.db.GetWeddingsForGroup(chatID)
	events := b.db.GetEventsForGroup(chatID)

	notifications := "❌ Выключены"
	if settings.NotificationsEnabled {
		notifications = "✅ Включены"
	}

	chatType := "Группа"
	if chat.Type == "private" {
		chatType = "Личный чат"
	}

	return fmt.Sprintf(`⚙️ *НАСТРОЙКИ АССИСТЕНТА*

*📋 Информация о чате:*
• ID чата: %s
• Название: %s
• Тип: %s

*🔔 Уведомления:*
• Статус: %s
• Время: %s

*📊 Статистика:*
• Дней рождения в этой группе: %d
• Свадеб: %d
• Событий: %d
• Всего групп в ассистенте: %d

*👑 Администратор:* @%s`,
		chatID, settings.ChatName, chatType, notifications, settings.NotificationTime,
		len(birthdays), len(weddings), len(events), stats["total_groups"],
		b.cfg.AdminUsername)
}

func (b *Bot) handleStatus(chatID string) string {
	settings := b.db.GetGroupSettings(chatID)
	stats := b.db.GetStatistics()
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	weddings := b.db.GetWeddingsForGroup(chatID)
	events := b.db.GetEventsForGroup(chatID)

	notifications := "❌ Выключены"
	if settings.NotificationsEnabled {
		notifications = "✅ Включены"
	}

	return fmt.Sprintf(`📊 *СТАТУС АССИСТЕНТА*

🔔 Уведомления: %s
⏰ Время: %s
👥 Групп: %d

🎂 Дни рождения: %d
💍 Свадьбы: %d
📅 События: %d`,
		notifications, settings.NotificationTime, stats["total_groups"],
		len(birthdays), len(weddings), len(events))
}

func (b *Bot) handleEnable(chatID string) string {
	b.db.SetNotificationsEnabled(chatID, true)

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("⚙️ Настройки", "show_settings"),
		),
	)

	msg := tgbotapi.NewMessage(b.getChatID(chatID), "✅ Уведомления успешно включены!\nТеперь бот будет присылать уведомления о днях рождения.")
	msg.ReplyMarkup = &keyboard
	b.api.Send(msg)

	if chatIDInt, err := strconv.ParseInt(chatID, 10, 64); err == nil && chatIDInt != 0 {
		b.sendThreeDaysReminders(chatIDInt, chatID)
	}

	return ""
}

func (b *Bot) handleDisable(chatID string) string {
	b.db.SetNotificationsEnabled(chatID, false)
	return "❌ Уведомления выключены.\nБот больше не будет присылать уведомления о днях рождения."
}

func (b *Bot) handleTime(chatID, args string) string {
	if args == "" {
		return "Использование: /время ЧЧ:ММ\nПример: /время 09:00"
	}

	if !isValidTime(args) {
		return "Неверный формат времени! Используйте ЧЧ:ММ (00:00 - 23:59)"
	}

	b.db.SetNotificationTime(chatID, args)
	b.scheduler.UpdateGroupJobTime(chatID)

	return fmt.Sprintf("✅ Время уведомлений установлено на %s", args)
}