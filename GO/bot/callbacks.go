package bot

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"infodriver/storage"
)

func (b *Bot) handleCallback(update tgbotapi.Update) {
	query := update.CallbackQuery
	if query == nil {
		return
	}

	b.api.Send(tgbotapi.NewCallback(query.ID, ""))

	data := query.Data
	chatID := strconv.FormatInt(query.Message.Chat.ID, 10)
	chatIDInt := query.Message.Chat.ID

	switch data {
	case "enable_notifications":
		b.db.SetNotificationsEnabled(chatID, true)
		b.sendEdit(chatIDInt, query.Message.MessageID, "✅ Уведомления включены!\nТеперь бот будет присылать уведомления о днях рождения.")
	case "disable_notifications":
		b.db.SetNotificationsEnabled(chatID, false)
		b.sendEdit(chatIDInt, query.Message.MessageID, "❌ Уведомления выключены.\nБот больше не будет присылать уведомления.")
	case "show_settings":
		b.sendSettingsWithKeyboard(chatID, query.Message.Chat)
		return
	case "back_to_main", "main_menu":
		b.sendMainMenu(query.Message.Chat.ID, query.Message.MessageID)
		return

	case "bd_menu":
		b.clearUserState(chatID)
		b.handleBirthdayMenu(chatID)
		return
	case "bd_add":
		b.setUserState(chatID, "add_birthday")
		b.sendBirthdayAddHelp(chatID, chatIDInt)
		return
	case "bd_list":
		b.sendReply(chatIDInt, 0, b.handleList(chatID))
		return
	case "bd_today":
		b.sendReply(chatIDInt, 0, b.handleToday(chatID))
		return
	case "bd_upcoming":
		b.sendReply(chatIDInt, 0, b.handleUpcoming(chatID))
		return
	case "bd_delete":
		b.setUserState(chatID, "delete_birthday")
		b.sendDeleteBirthdayHelp(chatID, chatIDInt)
		return
	case "bd_back", "bd_cancel":
		b.clearUserState(chatID)
		b.handleBirthdayMenu(chatID)
		return

	case "wed_menu":
		b.clearUserState(chatID)
		b.handleWeddingsMenu(chatID)
		return
	case "wed_add":
		b.setUserState(chatID, "add_wedding")
		b.sendWeddingAddHelp(chatID, chatIDInt)
		return
	case "wed_list":
		b.sendReply(chatIDInt, 0, b.handleWeddingsList(chatID))
		return
	case "wed_today":
		b.sendReply(chatIDInt, 0, b.handleWeddingToday(chatID))
		return
	case "wed_delete":
		b.setUserState(chatID, "delete_wedding")
		b.sendDeleteWeddingHelp(chatID, chatIDInt)
		return
	case "wed_back", "wed_cancel":
		b.clearUserState(chatID)
		b.handleWeddingsMenu(chatID)
		return

	case "evt_add":
		b.setUserState(chatID, "add_event")
		b.sendEventAddHelp(chatID, chatIDInt)
		return
	case "evt_list":
		b.sendReply(chatIDInt, 0, b.handleEventsList(chatID))
		return
	case "evt_delete":
		b.setUserState(chatID, "delete_event")
		b.sendDeleteEventHelp(chatID, chatIDInt)
		return
	case "evt_types":
		b.sendEventTypesHelp(chatID, chatIDInt)
		return
	case "evt_back", "evt_cancel":
		b.clearUserState(chatID)
		b.handleEventsMenu(chatID)
		return
	case "events_menu":
		b.handleEventsMenu(chatID)
		return

	default:
		if strings.HasPrefix(data, "set_time_") {
			timePart := strings.TrimPrefix(data, "set_time_")
			b.db.SetNotificationTime(chatID, timePart)
			b.scheduler.UpdateGroupJobTime(chatID)
			b.sendEdit(chatIDInt, query.Message.MessageID, fmt.Sprintf("✅ Время уведомлений установлено на %s", timePart))
		} else if strings.HasPrefix(data, "page_birthdays_") {
			b.handleBirthdayPagination(chatID, chatIDInt, query.Message.MessageID, data)
			return
		}
	}
}

func (b *Bot) sendEdit(chatID int64, messageID int, text string) {
	editMsg := tgbotapi.NewEditMessageText(chatID, messageID, text)
	editMsg.ParseMode = "Markdown"
	b.api.Send(&editMsg)
}

func (b *Bot) handleBirthdayPagination(chatID string, editChatID int64, messageID int, data string) {
	page := 0
	fmt.Sscanf(strings.TrimPrefix(data, "page_birthdays_"), "%d", &page)
	birthdays := b.db.GetBirthdaysForGroup(chatID)

	if len(birthdays) == 0 {
		b.api.Send(tgbotapi.NewEditMessageText(editChatID, messageID, "Нет дней рождения в этой группе."))
		return
	}

	pageSize := 10
	totalPages := (len(birthdays) + pageSize - 1) / pageSize

	if page < 0 {
		page = 0
	}
	if page >= totalPages {
		page = totalPages - 1
	}

	start := page * pageSize
	end := start + pageSize
	if end > len(birthdays) {
		end = len(birthdays)
	}

	monthNames := []string{"", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"}

	result := fmt.Sprintf("🎂 *Дни рождения* (страница %d/%d)\n\n", page+1, totalPages)
	index := start + 1

	birthdayList := make([]storage.Birthday, 0, len(birthdays))
	for _, bd := range birthdays {
		birthdayList = append(birthdayList, bd)
	}

	sort.Slice(birthdayList, func(i, j int) bool {
		if birthdayList[i].Month != birthdayList[j].Month {
			return birthdayList[i].Month < birthdayList[j].Month
		}
		return birthdayList[i].Day < birthdayList[j].Day
	})

	for i := start; i < end; i++ {
		bd := birthdayList[i]
		monthName := monthNames[bd.Month]
		if bd.Year > 0 {
			age := time.Now().Year() - bd.Year
			result += fmt.Sprintf("%d. %s - %d %s %d (Возраст: %d)\n", index, bd.Name, bd.Day, monthName, bd.Year, age)
		} else {
			result += fmt.Sprintf("%d. %s - %d %s\n", index, bd.Name, bd.Day, monthName)
		}
		index++
	}

	var prevButton, nextButton tgbotapi.InlineKeyboardButton
	if page > 0 {
		prevButton = tgbotapi.NewInlineKeyboardButtonData("◀️ Назад", fmt.Sprintf("page_birthdays_%d", page-1))
	}
	if page < totalPages-1 {
		nextButton = tgbotapi.NewInlineKeyboardButtonData("Вперед ▶️", fmt.Sprintf("page_birthdays_%d", page+1))
	}

	var row []tgbotapi.InlineKeyboardButton
	if prevButton.Text != "" && nextButton.Text != "" {
		row = []tgbotapi.InlineKeyboardButton{prevButton, nextButton}
	} else if prevButton.Text != "" {
		row = []tgbotapi.InlineKeyboardButton{prevButton}
	} else if nextButton.Text != "" {
		row = []tgbotapi.InlineKeyboardButton{nextButton}
	}

	keyboard := tgbotapi.NewInlineKeyboardMarkup(row)

	msg := tgbotapi.NewEditMessageText(editChatID, messageID, result)
	msg.ParseMode = "Markdown"
	msg.ReplyMarkup = &keyboard
	b.api.Send(msg)
}
