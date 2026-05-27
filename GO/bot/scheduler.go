package bot

import (
	"fmt"
	"log"
	"math/rand"
	"strings"
	"sync"
	"time"

	"infodriver/storage"
)

type Scheduler struct {
	db                   *storage.DB
	stopChan             chan struct{}
	restartChan          chan struct{}
	wg                   sync.WaitGroup
	mu                   sync.RWMutex
	activeJobs           map[string]time.Time
	eventJobs            map[string]*EventJob
	reminderJobs         map[string]*ReminderJob
	lastNotificationSent map[string]time.Time
	lastRestartCheck     time.Time
}

type EventJob struct {
	ChatID  string
	Name   string
	Type   string
	Time   string
	NextRun time.Time
	Text   string
}

type ReminderJob struct {
	ChatID  string
	Name   string
	Day    int
	Month  int
	Year   int
	Type   string
	NextRun time.Time
}

func NewScheduler(db *storage.DB) *Scheduler {
	return &Scheduler{
		db:                   db,
		stopChan:             make(chan struct{}),
		restartChan:          make(chan struct{}),
		activeJobs:           make(map[string]time.Time),
		eventJobs:            make(map[string]*EventJob),
		reminderJobs:         make(map[string]*ReminderJob),
		lastNotificationSent: make(map[string]time.Time),
		lastRestartCheck:     time.Now(),
	}
}

func (s *Scheduler) Start() {
	s.wg.Add(1)
	go s.run()
}

func (s *Scheduler) Stop() {
	close(s.stopChan)
	s.wg.Wait()
}

func (s *Scheduler) RestartChan() <-chan struct{} {
	return s.restartChan
}

func (s *Scheduler) run() {
	defer s.wg.Done()

	log.Printf("[SCHEDULER] Starting scheduler...")
	s.loadEventJobs()
	s.checkJobs()
	log.Printf("[SCHEDULER] Initial catch-up done")

	for {
		func() {
			defer func() {
				if r := recover(); r != nil {
					log.Printf("[SCHEDULER] Panic recovered: %v", r)
				}
			}()
			s.checkJobs()
		}()
		time.Sleep(30 * time.Second)

		select {
		case <-s.stopChan:
			log.Printf("[SCHEDULER] Stopped")
			return
		default:
		}
	}
}

func (s *Scheduler) loadEventJobs() {
	groups := s.db.GetGroupsWithNotifications()
	for _, chatID := range groups {
		s.SetupEventJobs(chatID)
	}
}

func (s *Scheduler) checkJobs() {
	now := time.Now()
	groups := s.db.GetGroupsWithNotifications()

	log.Printf("[SCHEDULER] Checking jobs at %s for %d groups", now.Format("15:04:05"), len(groups))

	s.checkDailyRestart(now)

	for _, chatID := range groups {
		s.checkDailyNotifications(chatID, now)
		s.checkEventJobs(chatID, now)
		s.checkReminderJobs(chatID, now)
	}
}

func (s *Scheduler) checkDailyRestart(now time.Time) {
	hour, minute := now.Hour(), now.Minute()

	if hour == 23 && minute == 30 {
		if now.Sub(s.lastRestartCheck) > 25*time.Minute {
			s.lastRestartCheck = now
			log.Printf("[SCHEDULER] Scheduled restart at 23:30, sending restart signal")
			select {
			case s.restartChan <- struct{}{}:
			default:
			}
		}
	}
}

func (s *Scheduler) checkDailyNotifications(chatID string, now time.Time) {
	settings := s.db.GetGroupSettings(chatID)
	
	if !settings.NotificationsEnabled {
		return
	}

	notificationTime, err := time.Parse("15:04", settings.NotificationTime)
	if err != nil {
		return
	}

	todayScheduled := time.Date(now.Year(), now.Month(), now.Day(), notificationTime.Hour(), notificationTime.Minute(), 0, 0, now.Location())

	key := "notify_" + chatID + "_" + now.Format("2006-01-02")
	
	s.mu.RLock()
	if _, exists := s.activeJobs[key]; exists {
		s.mu.RUnlock()
		return
	}
	s.mu.RUnlock()

	diff := now.Sub(todayScheduled)
	log.Printf("[SCHEDULER] Group %s: checking daily notify: now=%s, scheduled=%s, diff=%v", chatID, now.Format("15:04:05"), todayScheduled.Format("15:04:05"), diff)
	if diff >= 0 && diff <= 3*time.Minute {
		log.Printf("[SCHEDULER] Group %s: time matches, sending daily notification", chatID)
		s.mu.Lock()
		s.activeJobs[key] = now
		s.mu.Unlock()
		s.sendDailyNotifications(chatID)
	}
}

func (s *Scheduler) sendDailyNotifications(chatID string) {
	birthdays := s.db.GetBirthdaysForGroup(chatID)
	weddings := s.db.GetWeddingsForGroup(chatID)

	today := time.Now()
	var birthdayNames []string
	var weddingNames []string

	log.Printf("[SCHEDULER] Checking birthdays in group %s: count=%d", chatID, len(birthdays))

	for _, b := range birthdays {
		if b.Day == today.Day() && b.Month == int(today.Month()) {
			birthdayNames = append(birthdayNames, b.Name)
			log.Printf("[SCHEDULER] Found birthday today: %s", b.Name)
		}
	}

	for _, w := range weddings {
		if w.Day == today.Day() && w.Month == int(today.Month()) {
			weddingNames = append(weddingNames, w.Name)
			log.Printf("[SCHEDULER] Found wedding today: %s", w.Name)
		}
	}

	if len(birthdayNames) > 0 {
		message := fmt.Sprintf("🎉 Сегодня дни рождения у: %s! 🎂\n\n", strings.Join(birthdayNames, ", "))
		message += randomCongratulation()
		log.Printf("[SCHEDULER] Sending birthday notification: %s", message)
		go sendMessage(chatID, message)
	} else {
		log.Printf("[SCHEDULER] No birthdays today in group %s", chatID)
	}

	if len(weddingNames) > 0 {
		message := fmt.Sprintf("💍 Сегодня годовщины свадеб у: %s! 🎊\n\n", strings.Join(weddingNames, ", "))
		message += randomWeddingCongratulation()
		log.Printf("[SCHEDULER] Sending wedding notification: %s", message)
		go sendMessage(chatID, message)
	}
}

func (s *Scheduler) checkEventJobs(chatID string, now time.Time) {
	type triggered struct {
		key string
		job *EventJob
	}

	s.mu.RLock()
	var toTrigger []triggered
	for key, job := range s.eventJobs {
		if job.ChatID == chatID {
			log.Printf("[SCHEDULER] checkEventJobs event: key=%s name=%s nextRun=%s chatID=%s", key, job.Name, job.NextRun.Format("2006-01-02 15:04:05"), chatID)
			if now.After(job.NextRun) || now.Equal(job.NextRun) {
				toTrigger = append(toTrigger, triggered{key, job})
			}
		}
	}
	eventCount := 0
	for _, job := range s.eventJobs {
		if job.ChatID == chatID {
			eventCount++
		}
	}
	s.mu.RUnlock()

	log.Printf("[SCHEDULER] Group %s: checkEventJobs total=%d toTrigger=%d", chatID, eventCount, len(toTrigger))
	if len(toTrigger) > 0 {
		s.mu.Lock()
		for _, t := range toTrigger {
			if now.Sub(t.job.NextRun) > 10*time.Minute {
				log.Printf("[SCHEDULER] Skipping late trigger for %s (%.0fs past), rescheduling", t.key, now.Sub(t.job.NextRun).Seconds())
				s.rescheduleEvent(t.key, t.job)
			} else {
				go s.triggerEvent(t.job)
				s.rescheduleEvent(t.key, t.job)
			}
		}
		s.mu.Unlock()
	}
}

func (s *Scheduler) checkReminderJobs(chatID string, now time.Time) {
	type triggered struct {
		key string
		job *ReminderJob
	}

	s.mu.RLock()
	var toTrigger []triggered
	for key, job := range s.reminderJobs {
		if job.ChatID != chatID {
			continue
		}
		if now.After(job.NextRun) || now.Equal(job.NextRun) {
			toTrigger = append(toTrigger, triggered{key, job})
		}
	}
	s.mu.RUnlock()

	log.Printf("[SCHEDULER] Group %s: checkReminderJobs toTrigger=%d", chatID, len(toTrigger))
	if len(toTrigger) > 0 {
		s.mu.Lock()
		for _, t := range toTrigger {
			go s.triggerReminder(t.job)
			s.rescheduleReminder(t.key, t.job)
		}
		s.mu.Unlock()
	}
}

func (s *Scheduler) triggerEvent(job *EventJob) {
	message := job.Text
	if message == "" {
		message = fmt.Sprintf("%s начинается!", job.Name)
	}
	log.Printf("[SCHEDULER] Event triggered: %s - %s", job.Name, message)
	sendMessage(job.ChatID, message)
}

func (s *Scheduler) rescheduleEvent(key string, job *EventJob) {
	now := time.Now()

	switch job.Type {
	case "ежедневно":
		job.NextRun = job.NextRun.AddDate(0, 0, 1)
	case "еженедельно":
		job.NextRun = job.NextRun.AddDate(0, 0, 7)
	case "двухнедельно":
		job.NextRun = job.NextRun.AddDate(0, 0, 14)
	case "ежемесячно":
		job.NextRun = job.NextRun.AddDate(0, 1, 0)
	case "одноразово":
		delete(s.eventJobs, key)
		return
	}

	if job.NextRun.Before(now) {
		job.NextRun = now.Add(time.Second)
	}
}

func (s *Scheduler) triggerReminder(job *ReminderJob) {
	months := []string{"", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"}
	dateStr := fmt.Sprintf("%d %s", job.Day, months[job.Month])

	var message string
	if job.Type == "birthday" {
		message = fmt.Sprintf("🔔 Напоминание: Через 3 дня день рождения у %s (%s)!", job.Name, dateStr)
	} else {
		message = fmt.Sprintf("🔔 Напоминание: Через 3 дня годовщина свадьбы у %s (%s)!", job.Name, dateStr)
	}

	log.Printf("[SCHEDULER] Reminder triggered: %s", message)
	sendMessage(job.ChatID, message)
}

func (s *Scheduler) rescheduleReminder(key string, job *ReminderJob) {
	now := time.Now()
	nextYear := now.Year() + 1
	job.NextRun = time.Date(nextYear, time.Month(job.Month), job.Day, 9, 0, 0, 0, now.Location())
	job.NextRun = job.NextRun.AddDate(0, 0, -3)

	if job.NextRun.Before(now) {
		job.NextRun = job.NextRun.AddDate(1, 0, 0)
	}
}

func (s *Scheduler) SetupGroupJob(chatID string) {
	key := "group_" + chatID
	s.mu.Lock()
	s.activeJobs[key] = time.Now()
	s.mu.Unlock()
	log.Printf("[SCHEDULER] SetupGroupJob called for %s", chatID)
}

func (s *Scheduler) RemoveGroupJob(chatID string) {
	key := "group_" + chatID
	s.mu.Lock()
	delete(s.activeJobs, key)
	s.mu.Unlock()
}

func (s *Scheduler) UpdateGroupJobTime(chatID string) {
	log.Printf("[SCHEDULER] UpdateGroupJobTime called for %s", chatID)

	settings := s.db.GetGroupSettings(chatID)

	now := time.Now()
	today := now.Format("2006-01-02")
	key := "notify_" + chatID + "_" + today

	s.mu.Lock()
	delete(s.activeJobs, key)

	if settings.NotificationsEnabled {
		notificationTime, err := time.Parse("15:04", settings.NotificationTime)
		if err == nil {
			todayScheduled := time.Date(now.Year(), now.Month(), now.Day(), notificationTime.Hour(), notificationTime.Minute(), 0, 0, now.Location())
			if now.After(todayScheduled) && now.Sub(todayScheduled) <= 2*time.Hour {
				s.activeJobs[key] = now
				s.mu.Unlock()
				log.Printf("[SCHEDULER] Time %s already passed for today, sending immediately", settings.NotificationTime)
				go s.sendDailyNotifications(chatID)
				return
			}
		}
	}
	s.mu.Unlock()
}

func (s *Scheduler) SetupEventJobs(chatID string) {
	events := s.db.GetEventsForGroup(chatID)
	settings := s.db.GetGroupSettings(chatID)
	now := time.Now()

	s.mu.Lock()
	defer s.mu.Unlock()

	for key, event := range events {
		jobKey := fmt.Sprintf("event_%s_%s", chatID, key)
		if _, exists := s.eventJobs[jobKey]; exists {
			continue
		}

		nextRun := s.calculateNextEventRun(event.Type, event.Time, now, settings.NotificationTime)
		if nextRun.IsZero() {
			continue
		}

		job := &EventJob{
			ChatID:  chatID,
			Name:   event.Name,
			Type:   event.Type,
			Time:   event.Time,
			NextRun: nextRun,
			Text:   event.Text,
		}

		if event.Text == "" {
			job.Text = fmt.Sprintf("%s начинается!", event.Name)
		}

		s.eventJobs[jobKey] = job
		log.Printf("[SCHEDULER] Setup event job: %s, next run: %s", event.Name, nextRun.Format("2006-01-02 15:04:05"))
	}
}

func (s *Scheduler) calculateNextEventRun(eventType, timeStr string, now time.Time, defaultTime string) time.Time {
	// split by space (new format) or underscore (old format)
	parts := strings.Fields(timeStr)
	if len(parts) == 1 {
		parts = strings.Split(timeStr, "_")
	}

	switch eventType {
	case "ежедневно":
		hour, minute := parseTimeStr(timeStr)
		next := time.Date(now.Year(), now.Month(), now.Day(), hour, minute, 0, 0, now.Location())
		return next

	case "еженедельно", "двухнедельно":
		if len(parts) != 2 {
			return time.Time{}
		}
		dayName := strings.ToLower(parts[0])
		hour, minute := parseTimeStr(parts[1])

		dayNumbers := map[string]time.Weekday{
			"понедельник": time.Monday, "monday": time.Monday,
			"вторник": time.Tuesday, "tuesday": time.Tuesday,
			"среда": time.Wednesday, "wednesday": time.Wednesday,
			"четверг": time.Thursday, "thursday": time.Thursday,
			"пятница": time.Friday, "friday": time.Friday,
			"суббота": time.Saturday, "saturday": time.Saturday,
			"воскресенье": time.Sunday, "sunday": time.Sunday,
		}

		targetDay, ok := dayNumbers[dayName]
		if !ok {
			targetDay = time.Saturday
		}

		daysAhead := int(targetDay) - int(now.Weekday())
		next := now.AddDate(0, 0, daysAhead)
		next = time.Date(next.Year(), next.Month(), next.Day(), hour, minute, 0, 0, now.Location())
		if next.Before(now) || next.Equal(now) {
			next = next.AddDate(0, 0, 7)
		}
		if eventType == "двухнедельно" {
			next = next.AddDate(0, 0, 7)
		}
		return next

	case "ежемесячно":
		if len(parts) != 2 {
			return time.Time{}
		}
		day := parseInt(parts[0])
		hour, minute := parseTimeStr(parts[1])

		next := time.Date(now.Year(), now.Month(), day, hour, minute, 0, 0, now.Location())
		if next.Before(now) {
			if now.Month() == time.December {
				next = time.Date(now.Year()+1, time.January, day, hour, minute, 0, 0, now.Location())
			} else {
				next = time.Date(now.Year(), now.Month()+1, day, hour, minute, 0, 0, now.Location())
			}
		}
		return next

	case "одноразово":
		if len(parts) != 2 {
			return time.Time{}
		}
		datePart := parts[0]
		timePart := parts[1]

		dateParts := strings.Split(datePart, ".")
		if len(dateParts) != 3 {
			return time.Time{}
		}

		day := parseInt(dateParts[0])
		month := parseInt(dateParts[1])
		year := parseInt(dateParts[2])
		hour, minute := parseTimeStr(timePart)

		next := time.Date(year, time.Month(month), day, hour, minute, 0, 0, now.Location())
		if next.Before(now) {
			return time.Time{}
		}
		return next
	}

	return time.Time{}
}

func parseTimeStr(timeStr string) (int, int) {
	parts := strings.Split(timeStr, ":")
	if len(parts) != 2 {
		return 9, 0
	}
	return parseInt(parts[0]), parseInt(parts[1])
}

func parseInt(s string) int {
	var val int
	fmt.Sscanf(s, "%d", &val)
	return val
}

func (s *Scheduler) SetupThreeDaysReminder(chatID, name string, day, month, year int) {
	now := time.Now()
	birthDate := time.Date(now.Year(), time.Month(month), day, 9, 0, 0, 0, now.Location())
	if birthDate.Before(now) {
		birthDate = birthDate.AddDate(1, 0, 0)
	}

	reminderDate := birthDate.AddDate(0, 0, -3)
	if reminderDate.Before(now) {
		reminderDate = reminderDate.AddDate(1, 0, 0)
	}

	reminderType := "birthday"
	if strings.Contains(strings.ToLower(name), "свадьба") || strings.Contains(strings.ToLower(name), "wedding") {
		reminderType = "wedding"
	}

	job := &ReminderJob{
		ChatID:  chatID,
		Name:   name,
		Day:    day,
		Month:  month,
		Year:   year,
		Type:   reminderType,
		NextRun: reminderDate,
	}

	s.mu.Lock()
	key := fmt.Sprintf("reminder_%s_%s_%d_%d", reminderType, chatID, day, month)
	s.reminderJobs[key] = job
	s.mu.Unlock()

	log.Printf("[SCHEDULER] Setup 3-day reminder for %s on %s", name, reminderDate.Format("2006-01-02 15:04"))
}

func (s *Scheduler) RemoveEventJob(chatID, eventName string) {
	key := fmt.Sprintf("event_%s_%s", chatID, strings.ToLower(eventName))
	s.mu.Lock()
	delete(s.eventJobs, key)
	s.mu.Unlock()
}

func (s *Scheduler) RemoveReminderJob(chatID, name string, day, month int) {
	key := fmt.Sprintf("reminder_birthday_%s_%s_%d_%d", chatID, strings.ToLower(name), day, month)
	s.mu.Lock()
	delete(s.reminderJobs, key)
	key = fmt.Sprintf("reminder_wedding_%s_%s_%d_%d", chatID, strings.ToLower(name), day, month)
	delete(s.reminderJobs, key)
	s.mu.Unlock()
}

var globalSendFunc func(chatID, message string)
var getCongratulation func() string
var getWeddingWish func() string

func sendMessage(chatID, message string) {
	log.Printf("[SEND] Sending to %s: %s", chatID, message)
	if globalSendFunc != nil {
		globalSendFunc(chatID, message)
	} else {
		log.Printf("[SEND] No globalSendFunc set!")
	}
}

func SetSendFunc(f func(chatID, message string)) {
	globalSendFunc = f
	log.Printf("[SCHEDULER] SendFunc set")
}

func SetCongratulationFuncs(congFunc, weddingFunc func() string) {
	getCongratulation = congFunc
	getWeddingWish = weddingFunc
	log.Printf("[SCHEDULER] Congratulation funcs set")
}

func randomCongratulation() string {
	if getCongratulation != nil {
		return getCongratulation()
	}
	congratulations := []string{
		"🎊 С днем рождения! Желаем счастья, здоровья и радости!",
		"🎉 С днем рождения! Пусть все мечты сбываются!",
		"🎂 С днем рождения! Самые лучшие пожелания!",
		"🎊 Поздравляем! Желаем удачи и успехов!",
		"🎉 С днем рождения! Радости и любви!",
	}
	return congratulations[rand.Intn(len(congratulations))]
}

func randomWeddingCongratulation() string {
	if getWeddingWish != nil {
		return getWeddingWish()
	}
	congratulations := []string{
		"💝 С годовщиной свадьбы! Любви и счастья!",
		"💍 Поздравляем! Желаем долгих лет вместе!",
		"💕 С годовщиной! Пусть любовь никогда не угасает!",
	}
	return congratulations[rand.Intn(len(congratulations))]
}

func init() {
	log.SetFlags(0)
}