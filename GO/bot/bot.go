package bot

import (
	"fmt"
	"strconv"
	"strings"
	"sync"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"infodriver/logger"
	"infodriver/storage"
)

type Bot struct {
	api             *tgbotapi.BotAPI
	cfg             *Config
	db              *storage.DB
	scheduler       *Scheduler
	congratulations []string
	weddings        []string
	events          map[string]string
	mu              sync.RWMutex
	stopChan        chan struct{}
	userStates      map[string]string
	userStateMu     sync.RWMutex
}

type Config struct {
	BotToken      string
	Timezone      string
	AdminUsername string
	WishesFolder  string
}

func NewBot(cfg *Config, db *storage.DB) (*Bot, error) {
	api, err := tgbotapi.NewBotAPI(cfg.BotToken)
	if err != nil {
		return nil, err
	}

	bot := &Bot{
		api:        api,
		cfg:        cfg,
		db:         db,
		scheduler:  NewScheduler(db),
		stopChan:   make(chan struct{}),
		userStates: make(map[string]string),
	}

	bot.loadWishes()

	return bot, nil
}

func (b *Bot) loadWishes() {
	b.mu.Lock()

	b.congratulations = b.db.GetAllCongratulations()
	if len(b.congratulations) == 0 {
		b.congratulations = loadCongratulationsTexts()
		b.db.SeedWishesFromJSON(b.congratulations, nil)
	}

	b.weddings = b.db.GetAllWeddingWishes()
	if len(b.weddings) == 0 {
		b.weddings = loadWeddingTexts()
		b.db.SeedWishesFromJSON(nil, b.weddings)
	}

	b.reloadEvents()

	b.mu.Unlock()
}

func (b *Bot) ReloadEvents() {
	b.mu.Lock()
	b.reloadEvents()
	b.mu.Unlock()
}

func (b *Bot) reloadEvents() {
	b.events = b.db.GetAllEventTemplates()
	if len(b.events) == 0 {
		b.events = loadEventsMap(b.cfg.WishesFolder, "events.json")
		for key, text := range b.events {
			b.db.AddEventTemplate(key, text)
		}
	}
}

func (b *Bot) Start() error {
	fmt.Printf("[INFO] Bot started as @%s\n", b.api.Self.UserName)

	b.scheduler.Start()

	config := tgbotapi.UpdateConfig{
		Timeout: 45,
	}

	updates := b.api.GetUpdatesChan(config)

	for {
		select {
		case <-b.stopChan:
			b.scheduler.Stop()
			return nil
		case update := <-updates:
			if update.Message != nil {
				go b.handleMessage(update)
			} else if update.CallbackQuery != nil {
				go b.handleCallback(update)
			} else if update.MyChatMember != nil {
				go b.handleMyChatMember(update)
			}
		}
	}
}

func (b *Bot) handleMyChatMember(update tgbotapi.Update) {
	if update.MyChatMember == nil {
		return
	}

	chatID := strconv.FormatInt(update.MyChatMember.Chat.ID, 10)
	chatName := update.MyChatMember.Chat.Title

	newStatus := update.MyChatMember.NewChatMember.Status

	if newStatus == "member" || newStatus == "administrator" {
		b.db.UpdateGroupInfo(chatID, chatName)
		logger.Infof("[BOT] Bot added to group: %s (%s)", chatName, chatID)
	}

	if newStatus == "left" || newStatus == "kicked" {
		logger.Infof("[BOT] Bot removed from group: %s (%s)", chatName, chatID)
	}
}

func (b *Bot) Stop() {
	close(b.stopChan)
}

func (b *Bot) setUserState(chatID, state string) {
	b.userStateMu.Lock()
	defer b.userStateMu.Unlock()
	b.userStates[chatID] = state
}

func (b *Bot) getUserState(chatID string) string {
	b.userStateMu.RLock()
	defer b.userStateMu.RUnlock()
	return b.userStates[chatID]
}

func (b *Bot) clearUserState(chatID string) {
	b.userStateMu.Lock()
	defer b.userStateMu.Unlock()
	delete(b.userStates, chatID)
}

func (b *Bot) handleMessage(update tgbotapi.Update) {
	if update.Message == nil || update.Message.Text == "" {
		return
	}

	chatID := strconv.FormatInt(update.Message.Chat.ID, 10)
	text := update.Message.Text
	textLower := strings.ToLower(strings.TrimSpace(text))

	chatName := update.Message.Chat.Title
	if update.Message.Chat.Type == "private" && update.Message.From != nil {
		chatName = update.Message.From.FirstName
	}
	b.db.UpdateGroupInfo(chatID, chatName)

	if !strings.HasPrefix(textLower, "/") {
		b.handleUserInput(chatID, text, update.Message)
		return
	}

	b.clearUserState(chatID)

	parts := strings.SplitN(text, " ", 2)
	command := parts[0]
	args := ""
	if len(parts) > 1 {
		args = parts[1]
	}

	var response string

	switch strings.ToLower(command) {
	case "/start", "/старт":
		response = b.handleStart(chatID, update.Message.From)
	case "/help", "/справка":
		response = b.handleHelp()
	case "/settings", "/настройки":
		response = b.handleSettings(chatID, update.Message.Chat)
	case "/status", "/статус":
		response = b.handleStatus(chatID)
	case "/enable", "/включить":
		response = b.handleEnable(chatID)
	case "/disable", "/выключить":
		response = b.handleDisable(chatID)
	case "/time", "/время":
		response = b.handleTime(chatID, args)
	case "/add", "/добавить":
		response = b.handleAdd(chatID, args)
	case "/list", "/список":
		response = b.handleList(chatID)
	case "/delete", "/удалить":
		response = b.handleDelete(chatID, args)
	case "/today", "/сегодня":
		response = b.handleToday(chatID)
	case "/upcoming", "/ближайшие":
		response = b.handleUpcoming(chatID)
	case "/wedding", "/свадьба":
		response = b.handleWedding(chatID, args)
	case "/weddings", "/свадьбы":
		response = b.handleWeddingsMenu(chatID)
	case "/nowedding", "/несвадьба":
		response = b.handleNoWedding(chatID, args)
	case "/event", "/событие":
		response = b.handleEvent(chatID, args)
	case "/events", "/события":
		response = b.handleEventsMenu(chatID)
	case "/noevent", "/несобытие":
		response = b.handleNoEvent(chatID, args)
	case "/birthday", "/рождение":
		response = b.handleBirthdayMenu(chatID)
	case "/admin", "/админ":
		response = b.handleAdmin(chatID, update.Message.From, args)
	default:
		response = "Неизвестная команда! Используйте /справка для списка команд."
	}

	b.sendReply(update.Message.Chat.ID, update.Message.MessageID, response)
}

func (b *Bot) handleUserInput(chatID, text string, msg *tgbotapi.Message) {
	state := b.getUserState(chatID)
	if state == "" {
		return
	}

	b.clearUserState(chatID)

	var response string
	switch state {
	case "add_birthday":
		response = b.handleAdd(chatID, text)
	case "delete_birthday":
		response = b.handleDelete(chatID, text)
	case "add_wedding":
		response = b.handleWedding(chatID, text)
	case "delete_wedding":
		response = b.handleNoWedding(chatID, text)
	case "add_event":
		response = b.handleEvent(chatID, text)
	case "delete_event":
		response = b.handleNoEvent(chatID, text)
	}

	b.sendReply(msg.Chat.ID, msg.MessageID, response)
}