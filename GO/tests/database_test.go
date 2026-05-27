package tests

import (
	"os"
	"testing"

	"infodriver/storage"
)

func newTestDB(t *testing.T) *storage.DB {
	t.Helper()
	dir, err := os.MkdirTemp("", "infodriver_test_*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	t.Cleanup(func() { os.RemoveAll(dir) })

	db, err := storage.NewDB(dir)
	if err != nil {
		t.Fatalf("NewDB failed: %v", err)
	}
	return db
}

func TestNewDB(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	if db == nil {
		t.Fatal("NewDB returned nil")
	}
}

func TestGroupSettings(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID := "123456789"

	settings := db.GetGroupSettings(chatID)
	if settings == nil {
		t.Fatal("GetGroupSettings returned nil")
	}
	if settings.ChatID != chatID {
		t.Errorf("ChatID = %q, want %q", settings.ChatID, chatID)
	}
	if settings.NotificationTime != "10:00" {
		t.Errorf("NotificationTime = %q, want %q", settings.NotificationTime, "10:00")
	}

	settings = db.GetGroupSettings(chatID)
	if settings == nil {
		t.Fatal("GetGroupSettings returned nil on second call")
	}

	err := db.SetNotificationsEnabled(chatID, true)
	if err != nil {
		t.Fatalf("SetNotificationsEnabled failed: %v", err)
	}

	if !db.IsNotificationsEnabled(chatID) {
		t.Error("IsNotificationsEnabled = false, want true")
	}

	err = db.SetNotificationTime(chatID, "13:30")
	if err != nil {
		t.Fatalf("SetNotificationTime failed: %v", err)
	}
	if db.GetNotificationTime(chatID) != "13:30" {
		t.Errorf("GetNotificationTime = %q, want %q", db.GetNotificationTime(chatID), "13:30")
	}
}

func TestUpdateGroupInfo(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID := "999"
	err := db.UpdateGroupInfo(chatID, "Test Group")
	if err != nil {
		t.Fatalf("UpdateGroupInfo failed: %v", err)
	}

	settings := db.GetGroupSettings(chatID)
	if settings.ChatName != "Test Group" {
		t.Errorf("ChatName = %q, want %q", settings.ChatName, "Test Group")
	}
}

func TestBirthdayCRUD(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID := "111"

	ok := db.AddBirthday(chatID, "Иван", 15, 3, 1990)
	if !ok {
		t.Fatal("AddBirthday returned false")
	}

	ok = db.AddBirthday(chatID, "Иван", 15, 3, 1990)
	if ok {
		t.Error("AddBirthday duplicate returned true, want false")
	}

	birthdays := db.GetBirthdaysForGroup(chatID)
	if len(birthdays) != 1 {
		t.Fatalf("GetBirthdaysForGroup returned %d items, want 1", len(birthdays))
	}
	if birthdays["иван"].Name != "Иван" {
		t.Errorf("birthday name = %q, want %q", birthdays["иван"].Name, "Иван")
	}

	ok = db.RemoveBirthday(chatID, "Иван")
	if !ok {
		t.Fatal("RemoveBirthday returned false")
	}

	birthdays = db.GetBirthdaysForGroup(chatID)
	if len(birthdays) != 0 {
		t.Errorf("after delete, got %d birthdays, want 0", len(birthdays))
	}
}

func TestWeddingCRUD(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID := "222"

	ok := db.AddWedding(chatID, "Петр и Анна", 10, 6, 2015)
	if !ok {
		t.Fatal("AddWedding returned false")
	}

	ok = db.AddWedding(chatID, "Петр и Анна", 10, 6, 2015)
	if ok {
		t.Error("AddWedding duplicate returned true, want false")
	}

	weddings := db.GetWeddingsForGroup(chatID)
	if len(weddings) != 1 {
		t.Fatalf("GetWeddingsForGroup returned %d items, want 1", len(weddings))
	}

	ok = db.RemoveWedding(chatID, "Петр и Анна")
	if !ok {
		t.Fatal("RemoveWedding returned false")
	}

	weddings = db.GetWeddingsForGroup(chatID)
	if len(weddings) != 0 {
		t.Errorf("after delete, got %d weddings, want 0", len(weddings))
	}
}

func TestEventCRUD(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID := "333"

	ok := db.AddEvent(chatID, "утренник", "ежедневно", "09:00", "Утро начинается!")
	if !ok {
		t.Fatal("AddEvent returned false")
	}

	ok = db.AddEvent(chatID, "утренник", "ежедневно", "09:00", "Утро начинается!")
	if ok {
		t.Error("AddEvent duplicate returned true, want false")
	}

	events := db.GetEventsForGroup(chatID)
	if len(events) != 1 {
		t.Fatalf("GetEventsForGroup returned %d items, want 1", len(events))
	}
	if events["утренник"].Type != "ежедневно" {
		t.Errorf("event type = %q, want %q", events["утренник"].Type, "ежедневно")
	}

	ok = db.RemoveEvent(chatID, "утренник")
	if !ok {
		t.Fatal("RemoveEvent returned false")
	}

	events = db.GetEventsForGroup(chatID)
	if len(events) != 0 {
		t.Errorf("after delete, got %d events, want 0", len(events))
	}
}

func TestCongratulationsAndWishes(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	err := db.AddCongratulations("С днем рождения!")
	if err != nil {
		t.Fatalf("AddCongratulations failed: %v", err)
	}
	err = db.AddCongratulations("Поздравляем!")
	if err != nil {
		t.Fatalf("AddCongratulations failed: %v", err)
	}

	all := db.GetAllCongratulations()
	if len(all) != 2 {
		t.Errorf("GetAllCongratulations = %d items, want 2", len(all))
	}

	if db.GetCongratulationsCount() != 2 {
		t.Errorf("GetCongratulationsCount = %d, want 2", db.GetCongratulationsCount())
	}

	removed := db.RemoveCongratulations("С днем рождения!")
	if !removed {
		t.Fatal("RemoveCongratulations returned false")
	}

	all = db.GetAllCongratulations()
	if len(all) != 1 {
		t.Errorf("after delete, GetAllCongratulations = %d, want 1", len(all))
	}

	err = db.AddWeddingWish("Любви и счастья!")
	if err != nil {
		t.Fatalf("AddWeddingWish failed: %v", err)
	}

	wishes := db.GetAllWeddingWishes()
	if len(wishes) != 1 {
		t.Errorf("GetAllWeddingWishes = %d items, want 1", len(wishes))
	}

	if db.GetWeddingWishesCount() != 1 {
		t.Errorf("GetWeddingWishesCount = %d, want 1", db.GetWeddingWishesCount())
	}
}

func TestEventTemplates(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	err := db.AddEventTemplate("meeting_start", "Встреча начинается!")
	if err != nil {
		t.Fatalf("AddEventTemplate failed: %v", err)
	}

	templates := db.GetAllEventTemplates()
	if len(templates) != 1 {
		t.Errorf("GetAllEventTemplates = %d items, want 1", len(templates))
	}
	if templates["meeting_start"] != "Встреча начинается!" {
		t.Errorf("template text = %q, want %q", templates["meeting_start"], "Встреча начинается!")
	}

	err = db.RemoveEventTemplate("meeting_start")
	if err != nil {
		t.Fatalf("RemoveEventTemplate failed: %v", err)
	}

	templates = db.GetAllEventTemplates()
	if len(templates) != 0 {
		t.Errorf("after delete, GetAllEventTemplates = %d, want 0", len(templates))
	}
}

func TestGetGroupsWithNotifications(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID1 := "100"
	chatID2 := "200"

	db.UpdateGroupInfo(chatID1, "Group 1")
	db.UpdateGroupInfo(chatID2, "Group 2")

	db.SetNotificationsEnabled(chatID1, true)

	enabled := db.GetGroupsWithNotifications()
	found := false
	for _, id := range enabled {
		if id == chatID1 {
			found = true
		}
		if id == chatID2 {
			t.Error("chatID2 should not be in enabled groups")
		}
	}
	if !found {
		t.Error("chatID1 should be in enabled groups")
	}
}

func TestGetAllGroups(t *testing.T) {
	db := newTestDB(t)
	defer db.Close()

	chatID1 := "aaa"
	chatID2 := "bbb"
	db.UpdateGroupInfo(chatID1, "Alpha")
	db.UpdateGroupInfo(chatID2, "Beta")

	all := db.GetAllGroups()
	if len(all) < 2 {
		t.Errorf("GetAllGroups returned %d, want >=2", len(all))
	}
	if all["aaa"].ChatName != "Alpha" {
		t.Errorf("Alpha chat name = %q, want %q", all["aaa"].ChatName, "Alpha")
	}
}
