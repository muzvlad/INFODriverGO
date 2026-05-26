package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"runtime/debug"
	"strings"
	"syscall"
	"time"

	"infodriver/bot"
	"infodriver/server"
	"infodriver/storage"
)

func main() {
	for {
		runBot()
	}
}

func setMemoryLimit() {
	runtime.GOMAXPROCS(1)

	debug.SetGCPercent(50)

	log.Printf("[MAIN] Memory limits set: GOMAXPROCS=1, GC=50%%")
}

func runBot() {
	setMemoryLimit()

	loadEnvFile()

	os.MkdirAll("logs", 0755)
	logFile, err := os.OpenFile("logs/bot_"+time.Now().Format("2006-01-02")+".log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err == nil {
		log.SetOutput(logFile)
	}
	log.SetFlags(0)

	fmt.Println("========================================")
	fmt.Println("INFODriver Bot - Build OK")
	fmt.Println("========================================")
	fmt.Println()

	token := os.Getenv("BOT_TOKEN")
	if token == "" {
		fmt.Println("[ERROR] BOT_TOKEN not set!")
		fmt.Println("Set environment variable: set BOT_TOKEN=your_token")
		log.Fatalf("[ERROR] BOT_TOKEN not set!")
	}

	cfg := &bot.Config{
		BotToken:      token,
		Timezone:      getEnv("TIMEZONE", "Europe/Moscow"),
		AdminUsername: "muzvlad911",
		WishesFolder:  "wishes",
	}

	db, err := storage.NewDB(".")
	if err != nil {
		log.Fatalf("[ERROR] Database init failed: %v", err)
	}
	defer db.Close()

	log.Printf("[MAIN] Database initialized")

	telegramBot, err := bot.NewBot(cfg, db)
	if err != nil {
		log.Fatalf("[ERROR] Bot creation failed: %v", err)
	}

	bot.SetSendFunc(telegramBot.SendGroupNotification)

	fmt.Println("[OK] Bot initialized!")
	log.Printf("[MAIN] Bot initialized")

	bot.SetCongratulationFuncs(telegramBot.GetRandomCongratulation, telegramBot.GetRandomWeddingWish)

	apiPort := getEnv("API_PORT", "8080")
	apiToken := getEnv("API_TOKEN", "infodriver_secret_token")

	apiServer := server.NewServer(db, apiPort, apiToken)
	apiServer.SetOnTemplatesChanged(telegramBot.ReloadEvents)
	go func() {
		if err := apiServer.Start(); err != nil {
			log.Printf("[SERVER] API server error: %v", err)
		}
	}()

	go func() {
		if err := telegramBot.Start(); err != nil {
			fmt.Printf("[ERROR] Bot error: %v\n", err)
		}
	}()

	fmt.Printf("[OK] Bot started!\n")
	fmt.Printf("[OK] API server running on http://localhost:%s\n", apiPort)
	fmt.Println()
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println("========================================")

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	select {
	case <-quit:
		fmt.Println()
		fmt.Println("[STOP] Stopping bot...")
		telegramBot.Stop()
		fmt.Println("[OK] Bot stopped")
		return
	case <-telegramBot.Scheduler().RestartChan():
		fmt.Println()
		fmt.Println("[RESTART] Restarting bot...")
		telegramBot.Stop()
		fmt.Println("[OK] Bot stopped, restarting...")
		time.Sleep(2 * time.Second)
		cmd := exec.Command(os.Args[0])
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Start()
		os.Exit(0)
	}
}

func loadEnvFile() {
	envFile := ".env"
	file, err := os.Open(envFile)
	if err != nil {
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		if key != "" && os.Getenv(key) == "" {
			os.Setenv(key, value)
		}
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}