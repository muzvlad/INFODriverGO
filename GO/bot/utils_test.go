package bot

import (
	"testing"
	"time"
)

func TestParseDate(t *testing.T) {
	tests := []struct {
		input    string
		wantDay  int
		wantMon  int
		wantYear int
	}{
		{"15.03", 15, 3, 0},
		{"15.03.1990", 15, 3, 1990},
		{"01.01.2024", 1, 1, 2024},
		{"invalid", 0, 0, 0},
		{"13.13", 0, 0, 0},
		{"32.01", 0, 0, 0},
		{"0.5", 0, 0, 0},
		{"", 0, 0, 0},
	}
	for _, tc := range tests {
		d, m, y := parseDate(tc.input)
		if d != tc.wantDay || m != tc.wantMon || y != tc.wantYear {
			t.Errorf("parseDate(%q) = (%d,%d,%d), want (%d,%d,%d)", tc.input, d, m, y, tc.wantDay, tc.wantMon, tc.wantYear)
		}
	}
}

func TestIsValidTime(t *testing.T) {
	tests := []struct {
		input string
		want  bool
	}{
		{"10:00", true},
		{"23:59", true},
		{"00:00", true},
		{"24:00", false},
		{"10:60", false},
		{"abc", false},
		{"10:00:00", false},
		{"", false},
		{"-1:00", false},
	}
	for _, tc := range tests {
		got := isValidTime(tc.input)
		if got != tc.want {
			t.Errorf("isValidTime(%q) = %v, want %v", tc.input, got, tc.want)
		}
	}
}

func TestGetDaysUntil(t *testing.T) {
	now := time.Now()

	t.Run("future date returns positive", func(t *testing.T) {
		future := now.AddDate(0, 2, 0)
		got := getDaysUntil(future.Day(), int(future.Month()))
		if got < 55 || got > 65 {
			t.Errorf("getDaysUntil(~2 months ahead) = %d, want ~60", got)
		}
	})

	t.Run("past same-year date returns ~1 year", func(t *testing.T) {
		past := now.AddDate(0, -2, 0)
		got := getDaysUntil(past.Day(), int(past.Month()))
		if got < 300 || got > 370 {
			t.Errorf("getDaysUntil(~2 months ago) = %d, want ~305-365", got)
		}
	})
}
