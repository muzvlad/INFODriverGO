package bot

import (
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func (b *Bot) sendBirthdayAddHelp(chatID string, chatIDInt int64) {
	msg := "🎂 *Добавить день рождения*\n\n" +
		"Введите данные в формате:\n" +
		"`Имя ДД.ММ` или `Имя ДД.ММ.ГГГГ`\n\n" +
		"Пример: `Иван 15.03` или `Мария 22.08.1990`"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "bd_back"),
		),
	)

	b.sendMenu(chatIDInt, msg, &keyboard)
}

func (b *Bot) sendDeleteBirthdayHelp(chatID string, chatIDInt int64) {
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	if len(birthdays) == 0 {
		b.sendMenu(chatIDInt, "❌ Нет дней рождения для удаления.", nil)
		return
	}

	msg := "🗑️ *Удалить день рождения*\n\nВведите имя для удаления:"
	b.sendMenu(chatIDInt, msg, nil)
}

func (b *Bot) sendWeddingAddHelp(chatID string, chatIDInt int64) {
	msg := "💍 *Добавить годовщину свадьбы*\n\n" +
		"Введите данные в формате:\n" +
		"`Имя ДД.ММ` или `Имя ДД.ММ.ГГГГ`\n\n" +
		"Пример: `Анна 22.07`"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "wed_back"),
		),
	)

	b.sendMenu(chatIDInt, msg, &keyboard)
}

func (b *Bot) sendDeleteWeddingHelp(chatID string, chatIDInt int64) {
	weddings := b.db.GetWeddingsForGroup(chatID)
	if len(weddings) == 0 {
		b.sendMenu(chatIDInt, "❌ Нет свадеб для удаления.", nil)
		return
	}

	msg := "🗑️ *Удалить годовщину свадьбы*\n\nВведите имя для удаления:"
	b.sendMenu(chatIDInt, msg, nil)
}

func (b *Bot) sendEventAddHelp(chatID string, chatIDInt int64) {
	msg := "📅 *Добавить событие*\n\n" +
		"Введите: `тип время название`\n\n" +
		"*Типы:*\n" +
		"• `ежедневно ЧЧ:ММ название` - каждый день\n" +
		"• `еженедельно день ЧЧ:ММ название` - каждую неделю\n" +
		"• `ежемесячно ДД ЧЧ:ММ название` - каждый месяц\n" +
		"• `одноразово ДД.ММ.ГГГГ ЧЧ:ММ название` - один раз\n\n" +
		"Пример: `ежедневно 09:00 утро`"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "evt_back"),
		),
	)

	b.sendMenu(chatIDInt, msg, &keyboard)
}

func (b *Bot) sendDeleteEventHelp(chatID string, chatIDInt int64) {
	events := b.db.GetEventsForGroup(chatID)
	if len(events) == 0 {
		b.sendMenu(chatIDInt, "❌ Нет событий для удаления.", nil)
		return
	}

	msg := "🗑️ *Удалить событие*\n\nВведите название события:"
	b.sendMenu(chatIDInt, msg, nil)
}

func (b *Bot) sendEventTypesHelp(chatID string, chatIDInt int64) {
	msg := "📅 *Типы событий*\n\n" +
		"• `ежедневно ЧЧ:ММ` - каждый день\n" +
		"• `еженедельно день ЧЧ:ММ` - каждую неделю\n" +
		"• `двухнедельно день ЧЧ:ММ` - раз в 2 недели\n" +
		"• `ежемесячно ДД ЧЧ:ММ` - каждый месяц\n" +
		"• `одноразово ДД.ММ.ГГГГ ЧЧ:ММ` - один раз\n\n" +
		"Пример: `ежедневно 09:00 утро`"

	keyboard := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", "events_menu"),
		),
	)

	b.sendMenu(chatIDInt, msg, &keyboard)
}