package bot

import (
	"testing"
	"time"

	"infodriver/storage"
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

func TestGetTodaysBirthdays(t *testing.T) {
	today := time.Now()
	tomorrow := today.AddDate(0, 0, 1)

	birthdays := map[string]storage.Birthday{
		"ivan": {Name: "Иван", Day: today.Day(), Month: int(today.Month())},
		"petr": {Name: "Петр", Day: tomorrow.Day(), Month: int(tomorrow.Month())},
	}

	names := getTodaysBirthdays(birthdays)
	if len(names) != 1 || names[0] != "Иван" {
		t.Errorf("expected [Иван], got %v", names)
	}
}

func TestGetTodaysBirthdays_Empty(t *testing.T) {
	if names := getTodaysBirthdays(nil); len(names) != 0 {
		t.Errorf("expected empty from nil, got %v", names)
	}
	if names := getTodaysBirthdays(make(map[string]storage.Birthday)); len(names) != 0 {
		t.Errorf("expected empty from empty map, got %v", names)
	}
}

func TestGetTodaysWeddings(t *testing.T) {
	today := time.Now()
	yesterday := today.AddDate(0, 0, -1)

	weddings := map[string]storage.Wedding{
		"anna": {Name: "Анна", Day: today.Day(), Month: int(today.Month())},
		"olga": {Name: "Ольга", Day: yesterday.Day(), Month: int(yesterday.Month())},
	}

	names := getTodaysWeddings(weddings)
	if len(names) != 1 || names[0] != "Анна" {
		t.Errorf("expected [Анна], got %v", names)
	}
}

func TestSortBirthdaysByDate(t *testing.T) {
	birthdays := map[string]storage.Birthday{
		"mar": {Name: "Март", Month: 3, Day: 15},
		"jan": {Name: "Январь", Month: 1, Day: 10},
		"feb": {Name: "Февраль", Month: 2, Day: 20},
	}

	sorted := sortBirthdaysByDate(birthdays)
	if len(sorted) != 3 {
		t.Fatalf("expected 3, got %d", len(sorted))
	}
	if sorted[0].Name != "Январь" || sorted[1].Name != "Февраль" || sorted[2].Name != "Март" {
		t.Errorf("wrong order by month: %v", sorted)
	}
}

func TestSortBirthdaysByDate_SameMonth(t *testing.T) {
	birthdays := map[string]storage.Birthday{
		"ivan": {Name: "Иван", Month: 5, Day: 20},
		"petr": {Name: "Петр", Month: 5, Day: 10},
	}

	sorted := sortBirthdaysByDate(birthdays)
	if sorted[0].Name != "Петр" || sorted[1].Name != "Иван" {
		t.Errorf("wrong order within month: %v", sorted)
	}
}

func TestSortBirthdaysByDate_Empty(t *testing.T) {
	if sorted := sortBirthdaysByDate(nil); len(sorted) != 0 {
		t.Errorf("expected empty from nil, got %d", len(sorted))
	}
	if sorted := sortBirthdaysByDate(make(map[string]storage.Birthday)); len(sorted) != 0 {
		t.Errorf("expected empty from empty map, got %d", len(sorted))
	}
}

func TestSortWeddingsByDate(t *testing.T) {
	weddings := map[string]storage.Wedding{
		"jun": {Name: "Июнь", Month: 6, Day: 1},
		"apr": {Name: "Апрель", Month: 4, Day: 15},
	}

	sorted := sortWeddingsByDate(weddings)
	if len(sorted) != 2 {
		t.Fatalf("expected 2, got %d", len(sorted))
	}
	if sorted[0].Name != "Апрель" || sorted[1].Name != "Июнь" {
		t.Errorf("wrong order: %v", sorted)
	}
}
