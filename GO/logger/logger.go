package logger

import (
	"log"
	"os"
	"strings"
)

type Level int

const (
	DEBUG Level = iota
	INFO
	WARN
	ERROR
)

var currentLevel = INFO

func init() {
	Init()
}

func Init() {
	switch strings.ToUpper(os.Getenv("LOG_LEVEL")) {
	case "DEBUG":
		currentLevel = DEBUG
	case "INFO":
		currentLevel = INFO
	case "WARN":
		currentLevel = WARN
	case "ERROR":
		currentLevel = ERROR
	default:
		currentLevel = INFO
	}
}

func Debugf(format string, args ...interface{}) {
	if currentLevel <= DEBUG {
		log.Printf("[DEBUG] "+format, args...)
	}
}

func Infof(format string, args ...interface{}) {
	if currentLevel <= INFO {
		log.Printf("[INFO] "+format, args...)
	}
}

func Warnf(format string, args ...interface{}) {
	if currentLevel <= WARN {
		log.Printf("[WARN] "+format, args...)
	}
}

func Errorf(format string, args ...interface{}) {
	if currentLevel <= ERROR {
		log.Printf("[ERROR] "+format, args...)
	}
}

func Fatalf(format string, args ...interface{}) {
	Errorf(format, args...)
	os.Exit(1)
}
