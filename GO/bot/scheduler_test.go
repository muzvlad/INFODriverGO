package bot

import (
	"testing"
	"time"
)

func TestParseInt(t *testing.T) {
	tests := []struct {
		input string
		want  int
	}{
		{"0", 0},
		{"15", 15},
		{"09", 9},
		{"abc", 0},
		{"", 0},
		{"-5", -5},
	}
	for _, tc := range tests {
		got := parseInt(tc.input)
		if got != tc.want {
			t.Errorf("parseInt(%q) = %d, want %d", tc.input, got, tc.want)
		}
	}
}

func TestParseTimeStr(t *testing.T) {
	tests := []struct {
		input     string
		wantHour  int
		wantMin   int
	}{
		{"10:00", 10, 0},
		{"09:05", 9, 5},
		{"23:59", 23, 59},
		{"invalid", 9, 0},
		{"", 9, 0},
		{"10", 9, 0},
	}
	for _, tc := range tests {
		h, m := parseTimeStr(tc.input)
		if h != tc.wantHour || m != tc.wantMin {
			t.Errorf("parseTimeStr(%q) = (%d,%d), want (%d,%d)", tc.input, h, m, tc.wantHour, tc.wantMin)
		}
	}
}

func TestCalculateNextEventRun_Daily(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)

	next := s.calculateNextEventRun("ежедневно", "09:00", now, "10:00")
	expected := time.Date(2026, 5, 27, 9, 0, 0, 0, time.UTC)
	if !next.Equal(expected) {
		t.Errorf("daily 09:00 on 10:00 now: got %v, want %v", next, expected)
	}
}

func TestCalculateNextEventRun_Weekly(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)

	t.Run("next saturday 20:00", func(t *testing.T) {
		next := s.calculateNextEventRun("еженедельно", "суббота 20:00", now, "10:00")
		if next.Weekday() != time.Saturday || next.Hour() != 20 || next.Minute() != 0 {
			t.Errorf("unexpected next time: %v", next)
		}
		if next.Before(now) || next.Equal(now) {
			t.Errorf("next run %v should be after now %v", next, now)
		}
	})

	t.Run("monday 08:00 after saturday", func(t *testing.T) {
		saturday := time.Date(2026, 5, 30, 10, 0, 0, 0, time.UTC)
		next := s.calculateNextEventRun("еженедельно", "понедельник 08:00", saturday, "10:00")
		if next.Weekday() != time.Monday || next.Hour() != 8 {
			t.Errorf("unexpected next time: %v", next)
		}
		if next.Sub(saturday) > 72*time.Hour {
			t.Errorf("next run %v should be within 3 days of saturday %v", next, saturday)
		}
	})
}

func TestCalculateNextEventRun_Biweekly(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)

	next := s.calculateNextEventRun("двухнедельно", "суббота 20:00", now, "10:00")
	if next.Weekday() != time.Saturday || next.Hour() != 20 {
		t.Errorf("unexpected biweekly time: %v", next)
	}
	if next.Sub(now) < 7*24*time.Hour {
		t.Errorf("biweekly next run %v should be at least 7 days from now %v", next, now)
	}
}

func TestCalculateNextEventRun_Monthly(t *testing.T) {
	s := &Scheduler{}

	t.Run("15th 10:00 before now advances to next month", func(t *testing.T) {
		now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
		next := s.calculateNextEventRun("ежемесячно", "15 10:00", now, "10:00")
		expected := time.Date(2026, 6, 15, 10, 0, 0, 0, time.UTC)
		if !next.Equal(expected) {
			t.Errorf("got %v, want %v", next, expected)
		}
	})

	t.Run("15th 10:00 on same day returns same day", func(t *testing.T) {
		now := time.Date(2026, 5, 15, 9, 0, 0, 0, time.UTC)
		next := s.calculateNextEventRun("ежемесячно", "15 10:00", now, "10:00")
		expected := time.Date(2026, 5, 15, 10, 0, 0, 0, time.UTC)
		if !next.Equal(expected) {
			t.Errorf("got %v, want %v", next, expected)
		}
	})

	t.Run("december advances to january next year", func(t *testing.T) {
		now := time.Date(2026, 12, 27, 10, 0, 0, 0, time.UTC)
		next := s.calculateNextEventRun("ежемесячно", "15 10:00", now, "10:00")
		expected := time.Date(2027, 1, 15, 10, 0, 0, 0, time.UTC)
		if !next.Equal(expected) {
			t.Errorf("got %v, want %v", next, expected)
		}
	})
}

func TestCalculateNextEventRun_Oneshot(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)

	t.Run("future date returns that date", func(t *testing.T) {
		next := s.calculateNextEventRun("одноразово", "25.12.2026 12:00", now, "10:00")
		expected := time.Date(2026, 12, 25, 12, 0, 0, 0, time.UTC)
		if !next.Equal(expected) {
			t.Errorf("got %v, want %v", next, expected)
		}
	})

	t.Run("past date returns zero", func(t *testing.T) {
		next := s.calculateNextEventRun("одноразово", "25.12.2025 12:00", now, "10:00")
		if !next.IsZero() {
			t.Errorf("expected zero time for past event, got %v", next)
		}
	})

	t.Run("invalid format returns zero", func(t *testing.T) {
		next := s.calculateNextEventRun("одноразово", "invalid", now, "10:00")
		if !next.IsZero() {
			t.Errorf("expected zero time for invalid format, got %v", next)
		}
	})
}

func TestCalculateNextEventRun_UnknownType(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	next := s.calculateNextEventRun("unknown", "10:00", now, "10:00")
	if !next.IsZero() {
		t.Errorf("expected zero time for unknown type, got %v", next)
	}
}

func TestCalculateNextEventRun_WeeklyInvalidParts(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	next := s.calculateNextEventRun("еженедельно", "justonepart", now, "10:00")
	if !next.IsZero() {
		t.Errorf("expected zero time for invalid weekly parts, got %v", next)
	}
}

func TestCalculateNextEventRun_MonthlyInvalidParts(t *testing.T) {
	s := &Scheduler{}
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	next := s.calculateNextEventRun("ежемесячно", "singlepart", now, "10:00")
	if !next.IsZero() {
		t.Errorf("expected zero time for invalid monthly parts, got %v", next)
	}
}

func TestValidateEventTime(t *testing.T) {
	b := &Bot{}

	t.Run("daily valid", func(t *testing.T) {
		if err := b.validateEventTime("ежедневно", "09:00"); err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})
	t.Run("daily invalid", func(t *testing.T) {
		if err := b.validateEventTime("ежедневно", "invalid"); err == nil {
			t.Error("expected error")
		}
	})
	t.Run("weekly valid", func(t *testing.T) {
		if err := b.validateEventTime("еженедельно", "суббота 20:00"); err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})
	t.Run("weekly invalid", func(t *testing.T) {
		if err := b.validateEventTime("еженедельно", "invalid"); err == nil {
			t.Error("expected error")
		}
	})
	t.Run("biweekly valid", func(t *testing.T) {
		if err := b.validateEventTime("двухнедельно", "понедельник 10:00"); err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})
	t.Run("monthly valid", func(t *testing.T) {
		if err := b.validateEventTime("ежемесячно", "15 10:00"); err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})
	t.Run("monthly invalid", func(t *testing.T) {
		if err := b.validateEventTime("ежемесячно", "invalid"); err == nil {
			t.Error("expected error")
		}
	})
	t.Run("oneshot valid", func(t *testing.T) {
		if err := b.validateEventTime("одноразово", "25.12.2026 12:00"); err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})
	t.Run("oneshot invalid", func(t *testing.T) {
		if err := b.validateEventTime("одноразово", "25.12 12:00"); err == nil {
			t.Error("expected error for short date")
		}
	})
	t.Run("oneshot no parts", func(t *testing.T) {
		if err := b.validateEventTime("одноразово", "invalid"); err == nil {
			t.Error("expected error")
		}
	})
}

func TestRescheduleEvent_Daily(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	job := &EventJob{
		Name:    "test",
		Type:    "ежедневно",
		NextRun: now,
	}
	s.rescheduleEvent("event_test", job)
	expected := now.AddDate(0, 0, 1)
	if !job.NextRun.Equal(expected) {
		t.Errorf("daily: expected %v, got %v", expected, job.NextRun)
	}
}

func TestRescheduleEvent_Weekly(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	job := &EventJob{
		Name:    "test",
		Type:    "еженедельно",
		NextRun: now,
	}
	s.rescheduleEvent("event_test", job)
	expected := now.AddDate(0, 0, 7)
	if !job.NextRun.Equal(expected) {
		t.Errorf("weekly: expected %v, got %v", expected, job.NextRun)
	}
}

func TestRescheduleEvent_Biweekly(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	job := &EventJob{
		Name:    "test",
		Type:    "двухнедельно",
		NextRun: now,
	}
	s.rescheduleEvent("event_test", job)
	expected := now.AddDate(0, 0, 14)
	if !job.NextRun.Equal(expected) {
		t.Errorf("biweekly: expected %v, got %v", expected, job.NextRun)
	}
}

func TestRescheduleEvent_Monthly(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	job := &EventJob{
		Name:    "test",
		Type:    "ежемесячно",
		NextRun: now,
	}
	s.rescheduleEvent("event_test", job)
	expected := now.AddDate(0, 1, 0)
	if !job.NextRun.Equal(expected) {
		t.Errorf("monthly: expected %v, got %v", expected, job.NextRun)
	}
}

func TestRescheduleEvent_Oneshot(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	job := &EventJob{
		Name:    "test",
		Type:    "одноразово",
		NextRun: now,
	}
	s.eventJobs["event_test"] = job
	s.rescheduleEvent("event_test", job)
	if _, exists := s.eventJobs["event_test"]; exists {
		t.Error("oneshot job should be deleted after trigger")
	}
}

func TestRescheduleEvent_CatchUp(t *testing.T) {
	s := NewScheduler(nil)
	now := time.Date(2026, 5, 27, 10, 0, 0, 0, time.UTC)
	past := now.AddDate(0, 0, -2)
	job := &EventJob{
		Name:    "test",
		Type:    "ежедневно",
		NextRun: past,
	}
	s.rescheduleEvent("event_test", job)
	if job.NextRun.Before(now) {
		t.Errorf("rescheduled %v should not be before now %v", job.NextRun, now)
	}
}
