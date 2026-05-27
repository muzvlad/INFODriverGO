package tests

import (
	"bytes"
	"log"
	"os"
	"strings"
	"testing"

	"infodriver/logger"
)

func testWithLogLevel(t *testing.T, level string, fn func()) string {
	t.Helper()
	os.Setenv("LOG_LEVEL", level)
	// re-init logger to pick up new env
	logger.Init()

	var buf bytes.Buffer
	log.SetOutput(&buf)
	prevFlags := log.Flags()
	log.SetFlags(0)
	defer log.SetFlags(prevFlags)
	defer log.SetOutput(os.Stderr)

	fn()

	out := buf.String()
	// reset to default after test
	os.Setenv("LOG_LEVEL", "INFO")
	logger.Init()
	return out
}

func TestLoggerDebug(t *testing.T) {
	out := testWithLogLevel(t, "DEBUG", func() {
		logger.Debugf("debug msg %d", 1)
		logger.Infof("info msg %d", 2)
	})
	if !strings.Contains(out, "[DEBUG] debug msg 1") {
		t.Errorf("expected DEBUG output, got: %s", out)
	}
	if !strings.Contains(out, "[INFO] info msg 2") {
		t.Errorf("expected INFO output, got: %s", out)
	}
}

func TestLoggerInfo(t *testing.T) {
	out := testWithLogLevel(t, "INFO", func() {
		logger.Debugf("should be hidden")
		logger.Infof("should appear %d", 42)
	})
	if strings.Contains(out, "DEBUG") {
		t.Errorf("DEBUG output should be hidden at INFO level, got: %s", out)
	}
	if !strings.Contains(out, "[INFO] should appear 42") {
		t.Errorf("expected INFO output, got: %s", out)
	}
}

func TestLoggerWarn(t *testing.T) {
	out := testWithLogLevel(t, "WARN", func() {
		logger.Infof("should be hidden")
		logger.Warnf("warning msg")
		logger.Errorf("error msg")
	})
	if strings.Contains(out, "[INFO]") {
		t.Errorf("INFO output should be hidden at WARN level, got: %s", out)
	}
	if !strings.Contains(out, "[WARN] warning msg") {
		t.Errorf("expected WARN output, got: %s", out)
	}
	if !strings.Contains(out, "[ERROR] error msg") {
		t.Errorf("expected ERROR output, got: %s", out)
	}
}

func TestLoggerError(t *testing.T) {
	out := testWithLogLevel(t, "ERROR", func() {
		logger.Warnf("should be hidden")
		logger.Errorf("only error")
	})
	if strings.Contains(out, "[WARN]") {
		t.Errorf("WARN output should be hidden at ERROR level, got: %s", out)
	}
	if !strings.Contains(out, "[ERROR] only error") {
		t.Errorf("expected ERROR output, got: %s", out)
	}
}

func TestLoggerDefaultLevel(t *testing.T) {
	out := testWithLogLevel(t, "INVALID_LEVEL", func() {
		logger.Debugf("hidden")
		logger.Infof("visible")
	})
	if strings.Contains(out, "[DEBUG]") {
		t.Errorf("DEBUG should be hidden with default INFO level")
	}
	if !strings.Contains(out, "[INFO] visible") {
		t.Errorf("expected INFO output with default level")
	}
}

func TestLoggerNoOutputForDebugByDefault(t *testing.T) {
	out := testWithLogLevel(t, "", func() {
		logger.Debugf("hidden")
	})
	if out != "" {
		t.Errorf("expected no output for DEBUG with default level, got: %s", out)
	}
}
