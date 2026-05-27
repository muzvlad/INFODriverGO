package bot

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func parseDate(dateStr string) (int, int, int) {
	parts := strings.Split(dateStr, ".")
	if len(parts) < 2 {
		return 0, 0, 0
	}

	var day, month, year int
	fmt.Sscanf(parts[0], "%d", &day)
	fmt.Sscanf(parts[1], "%d", &month)
	if len(parts) >= 3 {
		fmt.Sscanf(parts[2], "%d", &year)
	}

	if day < 1 || day > 31 || month < 1 || month > 12 {
		return 0, 0, 0
	}

	return day, month, year
}

func isValidTime(timeStr string) bool {
	parts := strings.Split(timeStr, ":")
	if len(parts) != 2 {
		return false
	}

	var hour, minute int
	fmt.Sscanf(parts[0], "%d", &hour)
	fmt.Sscanf(parts[1], "%d", &minute)

	return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59
}

func getDaysUntil(day, month int) int {
	now := time.Now()
	thisYear := time.Date(now.Year(), time.Month(month), day, 0, 0, 0, 0, now.Location())

	if thisYear.Before(now) {
		thisYear = thisYear.AddDate(1, 0, 0)
	}

	return int(thisYear.Sub(now) / (24 * time.Hour))
}

func (b *Bot) GetRandomCongratulation() string {
	b.mu.RLock()
	defer b.mu.RUnlock()

	if len(b.congratulations) == 0 {
		return "🎉 С днем рождения! Желаем счастья и радости!"
	}
	return b.congratulations[rand.Intn(len(b.congratulations))]
}

func (b *Bot) GetRandomWeddingWish() string {
	b.mu.RLock()
	defer b.mu.RUnlock()

	if len(b.weddings) == 0 {
		return "💍 С годовщиной свадьбы! Любви и счастья!"
	}
	return b.weddings[rand.Intn(len(b.weddings))]
}

func (b *Bot) SendGroupNotification(chatID string, message string) {
	if id, err := strconv.ParseInt(chatID, 10, 64); err == nil {
		b.api.Send(tgbotapi.NewMessage(id, message))
	}
}

func (b *Bot) sendReply(chatID int64, replyTo int, text string) {
	if text == "" {
		return
	}
	msg := tgbotapi.NewMessage(chatID, text)
	if replyTo > 0 {
		msg.ReplyToMessageID = replyTo
	}
	b.api.Send(msg)
}

func (b *Bot) Scheduler() *Scheduler {
	return b.scheduler
}

func loadCongratulationsTexts() []string {
	data, err := os.ReadFile("wishes/congratulations.json")
	if err != nil {
		return []string{"С днем рождения! 🎂"}
	}

	var items []struct{ Text string }
	if err := json.Unmarshal(data, &items); err != nil {
		return []string{"С днем рождения! 🎂"}
	}

	texts := make([]string, len(items))
	for i, item := range items {
		texts[i] = item.Text
	}
	return texts
}

func loadWeddingTexts() []string {
	data, err := os.ReadFile("wishes/weddings.json")
	if err != nil {
		return []string{"С годовщиной свадьбы! 💍"}
	}

	var items []struct{ Text string }
	if err := json.Unmarshal(data, &items); err != nil {
		return []string{"С годовщиной свадьбы! 💍"}
	}

	texts := make([]string, len(items))
	for i, item := range items {
		texts[i] = item.Text
	}
	return texts
}

func loadEventsMap(wishesFolder, filename string) map[string]string {
	data, err := os.ReadFile(filepath.Join(wishesFolder, filename))
	if err != nil {
		return make(map[string]string)
	}

	type eventItem struct {
		Text string `json:"text"`
	}
	var raw map[string]eventItem
	if err := json.Unmarshal(data, &raw); err != nil {
		return make(map[string]string)
	}

	result := make(map[string]string)
	for k, v := range raw {
		result[k] = v.Text
	}
	return result
}