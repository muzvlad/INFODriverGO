package bot

import (
	"fmt"
	"math/rand"
	"sort"
	"strconv"
	"strings"
	"time"

	"infodriver/storage"
)

func (b *Bot) getChatID(chatID string) int64 {
	if id, err := strconv.ParseInt(chatID, 10, 64); err == nil {
		return id
	}
	return 0
}

func (b *Bot) sendThreeDaysReminders(chatID string) {
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	for _, bd := range birthdays {
		if bd.Year > 0 {
			b.scheduler.SetupThreeDaysReminder(chatID, bd.Name, bd.Day, bd.Month, bd.Year, "birthday")
		}
	}
}

func (b *Bot) handleAdd(chatID, args string) string {
	if args == "" {
		return "Использование: /добавить Имя ДД.ММ\nПример: /добавить Иван 15.03"
	}

	parts := strings.SplitN(args, " ", 2)
	if len(parts) < 2 {
		return "Использование: /добавить Имя ДД.ММ"
	}

	name := parts[0]
	dateStr := parts[1]

	day, month, year := parseDate(dateStr)
	if day == 0 || month == 0 {
		return "Неверный формат даты! Используйте ДД.ММ или ДД.ММ.ГГГГ"
	}

	if b.db.AddBirthday(chatID, name, day, month, year) {
		msg := fmt.Sprintf("✅ День рождения %s добавлен!", name)
		if year > 0 {
			msg = fmt.Sprintf("✅ День рождения %s (%02d.%02d.%d) добавлен!", name, day, month, year)
		}

		if year > 0 {
			b.scheduler.SetupThreeDaysReminder(chatID, name, day, month, year, "birthday")
		}

		return msg
	}
	return fmt.Sprintf("❌ День рождения %s уже существует!", name)
}

func (b *Bot) handleList(chatID string) string {
	birthdays := b.db.GetBirthdaysForGroup(chatID)

	if len(birthdays) == 0 {
		return "❌ Нет дней рождения в этой группе."
	}

	birthdayList := sortBirthdaysByDate(birthdays)

	result := "🎂 *Дни рождения:*\n\n"
	for i, bd := range birthdayList {
		monthName := monthNames[bd.Month]
		if bd.Year > 0 {
			age := time.Now().Year() - bd.Year
			result += fmt.Sprintf("%d. %s - %d %s %d (Возраст: %d)\n", i+1, bd.Name, bd.Day, monthName, bd.Year, age)
		} else {
			result += fmt.Sprintf("%d. %s - %d %s\n", i+1, bd.Name, bd.Day, monthName)
		}
	}

	return result
}

func (b *Bot) handleDelete(chatID, args string) string {
	if args == "" {
		return "Использование: /удалить Имя"
	}

	birthdays := b.db.GetBirthdaysForGroup(chatID)
	key := strings.ToLower(args)
	if bd, exists := birthdays[key]; exists {
		b.scheduler.RemoveReminderJob(chatID, bd.Name, bd.Day, bd.Month)
	}

	if b.db.RemoveBirthday(chatID, args) {
		return fmt.Sprintf("✅ День рождения %s удален!", args)
	}
	return fmt.Sprintf("❌ День рождения %s не найден!", args)
}

func (b *Bot) handleToday(chatID string) string {
	birthdays := b.db.GetBirthdaysForGroup(chatID)
	weddings := b.db.GetWeddingsForGroup(chatID)

	birthdayList := getTodaysBirthdays(birthdays)
	weddingList := getTodaysWeddings(weddings)

	if len(birthdayList) == 0 && len(weddingList) == 0 {
		return "🎉 Сегодня нет дней рождения и свадеб!"
	}

	result := ""
	if len(birthdayList) > 0 {
		result += fmt.Sprintf("🎂 *Сегодня дни рождения:* %s!\n\n", strings.Join(birthdayList, ", "))
	}
	if len(weddingList) > 0 {
		result += fmt.Sprintf("💍 *Сегодня годовщины свадеб:* %s!\n\n", strings.Join(weddingList, ", "))
	}

	b.mu.RLock()
	congratLen := len(b.congratulations)
	if congratLen > 0 {
		congrat := b.congratulations[rand.Intn(congratLen)]
		b.mu.RUnlock()
		result += fmt.Sprintf("🎊 %s", congrat)
	} else {
		b.mu.RUnlock()
	}

	return result
}

func (b *Bot) handleUpcoming(chatID string) string {
	birthdays := b.db.GetBirthdaysForGroup(chatID)

	type upcoming struct {
		bd        storage.Birthday
		daysUntil int
	}

	var upcomingList []upcoming
	for _, bd := range birthdays {
		daysUntil := getDaysUntil(bd.Day, bd.Month)
		if daysUntil >= 0 && daysUntil <= 7 {
			upcomingList = append(upcomingList, upcoming{bd, daysUntil})
		}
	}

	if len(upcomingList) == 0 {
		return "📅 Нет дней рождения в ближайшие 7 дней."
	}

	sort.Slice(upcomingList, func(i, j int) bool {
		return upcomingList[i].daysUntil < upcomingList[j].daysUntil
	})

	result := "📅 *Ближайшие дни рождения (7 дней):*\n\n"
	for i, u := range upcomingList {
		monthName := monthNames[u.bd.Month]
		if u.daysUntil == 0 {
			result += fmt.Sprintf("%d. %s - *СЕГОДНЯ!*\n", i+1, u.bd.Name)
		} else if u.daysUntil == 1 {
			result += fmt.Sprintf("%d. %s - завтра (%d %s)\n", i+1, u.bd.Name, u.bd.Day, monthName)
		} else {
			result += fmt.Sprintf("%d. %s - через %d дн. (%d %s)\n", i+1, u.bd.Name, u.daysUntil, u.bd.Day, monthName)
		}
	}

	return result
}

func (b *Bot) handleWedding(chatID, args string) string {
	if args == "" {
		return "Использование: /свадьба Имя ДД.ММ\nПример: /свадьба Иван 15.03"
	}

	parts := strings.SplitN(args, " ", 2)
	if len(parts) < 2 {
		return "Использование: /свадьба Имя ДД.ММ"
	}

	name := parts[0]
	dateStr := parts[1]

	day, month, year := parseDate(dateStr)
	if day == 0 || month == 0 {
		return "Неверный формат даты! Используйте ДД.ММ"
	}

	if b.db.AddWedding(chatID, name, day, month, year) {
		msg := fmt.Sprintf("✅ Годовщина свадьбы %s добавлена!", name)
		if year > 0 {
			msg = fmt.Sprintf("✅ Годовщина свадьбы %s (%02d.%02d.%d) добавлена!", name, day, month, year)
		}

		if year > 0 {
			b.scheduler.SetupThreeDaysReminder(chatID, name, day, month, year, "wedding")
		}

		return msg
	}
	return fmt.Sprintf("❌ Годовщина свадьбы %s уже существует!", name)
}

func (b *Bot) handleWeddingsList(chatID string) string {
	weddings := b.db.GetWeddingsForGroup(chatID)

	if len(weddings) == 0 {
		return "❌ Нет годовщин свадеб в этой группе."
	}

	weddingList := sortWeddingsByDate(weddings)

	result := "💍 *Годовщины свадеб:*\n\n"
	for i, w := range weddingList {
		monthName := monthNames[w.Month]
		if w.Year > 0 {
			years := time.Now().Year() - w.Year
			result += fmt.Sprintf("%d. %s - %d %s %d (%d лет)\n", i+1, w.Name, w.Day, monthName, w.Year, years)
		} else {
			result += fmt.Sprintf("%d. %s - %d %s\n", i+1, w.Name, w.Day, monthName)
		}
	}

	return result
}

func (b *Bot) handleNoWedding(chatID, args string) string {
	if args == "" {
		return "Использование: /несвадьба Имя"
	}

	weddings := b.db.GetWeddingsForGroup(chatID)
	key := strings.ToLower(args)
	if w, exists := weddings[key]; exists {
		b.scheduler.RemoveReminderJob(chatID, w.Name, w.Day, w.Month)
	}

	if b.db.RemoveWedding(chatID, args) {
		return fmt.Sprintf("✅ Годовщина свадьбы %s удалена!", args)
	}
	return fmt.Sprintf("❌ Годовщина свадьбы %s не найдена!", args)
}

func (b *Bot) handleWeddingToday(chatID string) string {
	weddings := b.db.GetWeddingsForGroup(chatID)

	weddingList := getTodaysWeddings(weddings)

	if len(weddingList) == 0 {
		return "💍 Сегодня нет годовщин свадеб!"
	}

	result := "💍 *Сегодня годовщины свадеб:* " + strings.Join(weddingList, ", ") + "!\n\n"
	b.mu.RLock()
	wedLen := len(b.weddings)
	if wedLen > 0 {
		result += b.weddings[rand.Intn(wedLen)]
	}
	b.mu.RUnlock()
	return result
}

func (b *Bot) handleEvent(chatID, args string) string {
	if args == "" {
		return `📅 *Использование: /событие тип время название*
	
*Типы:*
• ежедневно ЧЧ:ММ название
• еженедельно день ЧЧ:ММ название
• ежемесячно ДД ЧЧ:ММ название
• одноразово ДД.ММ.ГГГГ ЧЧ:ММ название

Пример: /событие ежедневно 09:00 утро`
	}

	parts := strings.SplitN(args, " ", 2)
	if len(parts) < 2 {
		return "Неверный формат! Используйте: /событие тип время название"
	}

	eventType := strings.ToLower(parts[0])
	rest := strings.TrimSpace(parts[1])

	validTypes := map[string]bool{
		"ежедневно": true, "еженедельно": true, "двухнедельно": true, "ежемесячно": true, "одноразово": true,
	}

	if !validTypes[eventType] {
		return "Неверный тип! Доступные: ежедневно, еженедельно, двухнедельно, ежемесячно, одноразово"
	}

	restParts := strings.Fields(rest)

	timeWords := 2
	if eventType == "ежедневно" {
		timeWords = 1
	}

	if len(restParts) < timeWords {
		return "Неверный формат! Используйте: /событие тип время название"
	}

	timeStr := strings.Join(restParts[:timeWords], " ")
	eventName := strings.Join(restParts[timeWords:], " ")
	if eventName == "" {
		return "Неверный формат! Используйте: /событие тип время название"
	}

	if err := b.validateEventTime(eventType, timeStr); err != nil {
		return err.Error()
	}

	b.mu.RLock()
	eventText := b.events[strings.ToLower(eventName)]
	b.mu.RUnlock()
	if eventText == "" {
		eventText = fmt.Sprintf("%s начинается!", eventName)
	}

	b.db.AddEvent(chatID, eventName, eventType, timeStr, eventText)
	b.scheduler.SetupEventJobs(chatID)

	return fmt.Sprintf("✅ Событие '%s' (%s) добавлено!", eventName, eventType)
}

func (b *Bot) validateEventTime(eventType, timeStr string) error {
	switch eventType {
	case "ежедневно":
		parts := strings.Split(timeStr, ":")
		if len(parts) != 2 {
			return fmt.Errorf("неверный формат для ежедневного события! Используйте ЧЧ:ММ")
		}
	case "еженедельно", "двухнедельно":
		parts := strings.Fields(timeStr)
		if len(parts) != 2 {
			return fmt.Errorf("неверный формат! Используйте: день ЧЧ:ММ (например: суббота 20:00)")
		}
	case "ежемесячно":
		parts := strings.Fields(timeStr)
		if len(parts) != 2 {
			return fmt.Errorf("неверный формат! Используйте: ДД ЧЧ:ММ (например: 15 10:00)")
		}
	case "одноразово":
		parts := strings.Fields(timeStr)
		if len(parts) != 2 {
			return fmt.Errorf("неверный формат! Используйте: ДД.ММ.ГГГГ ЧЧ:ММ (например: 25.12.2026 12:00)")
		}
		dateParts := strings.Split(parts[0], ".")
		if len(dateParts) != 3 {
			return fmt.Errorf("неверный формат даты! Используйте ДД.ММ.ГГГГ (например: 25.12.2026)")
		}
	}
	return nil
}

func (b *Bot) handleEventsList(chatID string) string {
	events := b.db.GetEventsForGroup(chatID)

	if len(events) == 0 {
		return "❌ Нет событий в этой группе."
	}

	typeNames := map[string]string{
		"ежедневно":   "📅 Ежедневно",
		"еженедельно": "📅 Еженедельно",
		"двухнедельно": "📅 Раз в 2 недели",
		"ежемесячно": "📅 Ежемесячно",
		"одноразово": "📅 Одноразово",
	}

	result := "📅 *События:*\n\n"

	eventList := make([]storage.Event, 0, len(events))
	for _, e := range events {
		eventList = append(eventList, e)
	}

	for _, e := range eventList {
		typeName := typeNames[e.Type]
		if typeName == "" {
			typeName = e.Type
		}
		result += fmt.Sprintf("• *%s* - %s в %s\n", e.Name, typeName, e.Time)
	}

	return result
}

func (b *Bot) handleNoEvent(chatID, args string) string {
	if args == "" {
		return "Использование: /несобытие Название"
	}

	if b.db.RemoveEvent(chatID, args) {
		b.scheduler.RemoveEventJob(chatID, args)
		return fmt.Sprintf("✅ Событие '%s' удалено!", args)
	}
	return fmt.Sprintf("❌ Событие '%s' не найдено!", args)
}