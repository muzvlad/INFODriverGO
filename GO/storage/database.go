package storage

import (
	"database/sql"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	_ "modernc.org/sqlite"
	"infodriver/logger"
)

type DB struct {
	db            *sql.DB
	mu            sync.RWMutex
	path          string
	settingsCache map[string]*GroupSettings
}

type GroupSettings struct {
	ChatID               string `json:"chat_id"`
	ChatName             string `json:"chat_name"`
	NotificationsEnabled bool   `json:"notifications_enabled"`
	NotificationTime     string `json:"notification_time"`
	Timezone             string `json:"timezone"`
	LastUpdated          string `json:"last_updated"`
}

type Birthday struct {
	ID     int64  `json:"id"`
	ChatID string `json:"chat_id"`
	Name   string `json:"name"`
	Day    int    `json:"day"`
	Month  int    `json:"month"`
	Year   int    `json:"year"`
}

type Wedding struct {
	ID     int64  `json:"id"`
	ChatID string `json:"chat_id"`
	Name   string `json:"name"`
	Day    int    `json:"day"`
	Month  int    `json:"month"`
	Year   int    `json:"year"`
}

type Event struct {
	ID     int64  `json:"id"`
	ChatID string `json:"chat_id"`
	Name   string `json:"name"`
	Type   string `json:"type"`
	Time   string `json:"time"`
	Text   string `json:"text"`
}

func NewDB(basePath string) (*DB, error) {
	dbPath := filepath.Join(basePath, "bot.db")

	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(12)

	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		logger.Errorf("[DB] WAL pragma error: %v", err)
	}
	if _, err := db.Exec("PRAGMA synchronous=NORMAL"); err != nil {
		logger.Errorf("[DB] synchronous pragma error: %v", err)
	}
	if _, err := db.Exec("PRAGMA busy_timeout=5000"); err != nil {
		logger.Errorf("[DB] busy_timeout pragma error: %v", err)
	}

	if err := db.Ping(); err != nil {
		return nil, err
	}

	database := &DB{db: db, path: dbPath, settingsCache: make(map[string]*GroupSettings)}

	if err := database.init(); err != nil {
		return nil, err
	}

	if _, err := os.Stat(dbPath); os.IsNotExist(err) {
		database.seedDefaultData()
	}

	return database, nil
}

func (d *DB) init() error {
	schema := `
	CREATE TABLE IF NOT EXISTS groups (
		chat_id TEXT PRIMARY KEY,
		chat_name TEXT,
		notifications_enabled INTEGER DEFAULT 0,
		notification_time TEXT DEFAULT '10:00',
		timezone TEXT DEFAULT 'Europe/Moscow',
		last_updated TEXT
	);

	CREATE TABLE IF NOT EXISTS birthdays (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		chat_id TEXT,
		name TEXT,
		day INTEGER,
		month INTEGER,
		year INTEGER DEFAULT 0,
		UNIQUE(chat_id, name)
	);

	CREATE TABLE IF NOT EXISTS weddings (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		chat_id TEXT,
		name TEXT,
		day INTEGER,
		month INTEGER,
		year INTEGER DEFAULT 0,
		UNIQUE(chat_id, name)
	);

	CREATE TABLE IF NOT EXISTS events (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		chat_id TEXT,
		name TEXT,
		type TEXT,
		time TEXT,
		text TEXT,
		UNIQUE(chat_id, name)
	);

	CREATE TABLE IF NOT EXISTS congratulations (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		text TEXT NOT NULL,
		is_active INTEGER DEFAULT 1,
		created_at TEXT DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS wedding_wishes (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		text TEXT NOT NULL,
		is_active INTEGER DEFAULT 1,
		created_at TEXT DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS event_templates (
		key TEXT PRIMARY KEY,
		text TEXT NOT NULL
	);

	CREATE INDEX IF NOT EXISTS idx_birthdays_chat ON birthdays(chat_id);
	CREATE INDEX IF NOT EXISTS idx_weddings_chat ON weddings(chat_id);
	CREATE INDEX IF NOT EXISTS idx_events_chat ON events(chat_id);
	CREATE INDEX IF NOT EXISTS idx_congratulations_active ON congratulations(is_active);
	CREATE INDEX IF NOT EXISTS idx_wedding_wishes_active ON wedding_wishes(is_active);
	`

	_, err := d.db.Exec(schema)
	return err
}

func (d *DB) seedDefaultData() {
	defaultGroups := []string{"249204598", "-5022355991", "-1003256918151", "-1002639028563", "-1001234567890"}
	for _, chatID := range defaultGroups {
		if _, err := d.db.Exec(`INSERT OR IGNORE INTO groups (chat_id, chat_name, notification_time, last_updated) VALUES (?, ?, '10:00', ?)`,
			chatID, "Группа "+chatID, time.Now().Format(time.RFC3339)); err != nil {
			logger.Errorf("[DB] seedDefaultData error: %v", err)
		}
	}
}

func (d *DB) Close() error {
	return d.db.Close()
}

func (d *DB) GetGroupSettings(chatID string) *GroupSettings {
	d.mu.RLock()
	s, ok := d.settingsCache[chatID]
	d.mu.RUnlock()
	if ok {
		return s
	}

	d.mu.Lock()
	defer d.mu.Unlock()

	if s, ok := d.settingsCache[chatID]; ok {
		return s
	}

	var settings GroupSettings
	err := d.db.QueryRow(`
		SELECT chat_id, chat_name, notifications_enabled, notification_time, timezone, last_updated 
		FROM groups WHERE chat_id = ?`, chatID).Scan(
		&settings.ChatID, &settings.ChatName, &settings.NotificationsEnabled,
		&settings.NotificationTime, &settings.Timezone, &settings.LastUpdated)

	if err == sql.ErrNoRows {
		return d.createGroupLocked(chatID, "Группа "+chatID)
	}
	if err != nil {
		logger.Errorf("[DB] GetGroupSettings error: %v", err)
		s := &GroupSettings{ChatID: chatID, ChatName: "Группа " + chatID, NotificationTime: "10:00"}
		d.settingsCache[chatID] = s
		return s
	}

	if settings.NotificationTime == "" {
		settings.NotificationTime = "10:00"
	}

	d.settingsCache[chatID] = &settings
	return &settings
}

func (d *DB) createGroupLocked(chatID, chatName string) *GroupSettings {
	now := time.Now().Format(time.RFC3339)
	if _, err := d.db.Exec(`INSERT OR IGNORE INTO groups (chat_id, chat_name, notifications_enabled, notification_time, timezone, last_updated) 
		VALUES (?, ?, 0, '10:00', 'Europe/Moscow', ?)`, chatID, chatName, now); err != nil {
		logger.Errorf("[DB] createGroup error: %v", err)
	}

	s := &GroupSettings{
		ChatID:               chatID,
		ChatName:             chatName,
		NotificationsEnabled: false,
		NotificationTime:     "10:00",
		Timezone:             "Europe/Moscow",
		LastUpdated:          now,
	}
	d.settingsCache[chatID] = s
	return s
}

func (d *DB) UpdateGroupInfo(chatID, chatName string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if _, err := d.db.Exec(`INSERT OR IGNORE INTO groups (chat_id, chat_name, notification_time, last_updated) VALUES (?, ?, '10:00', ?)`,
		chatID, chatName, time.Now().Format(time.RFC3339)); err != nil {
		logger.Errorf("[DB] UpdateGroupInfo insert error: %v", err)
	}

	_, err := d.db.Exec(`UPDATE groups SET chat_name = ?, last_updated = ? WHERE chat_id = ?`,
		chatName, time.Now().Format(time.RFC3339), chatID)
	if err != nil {
		logger.Errorf("[DB] UpdateGroupInfo update error: %v", err)
		return err
	}
	delete(d.settingsCache, chatID)
	return nil
}

func (d *DB) SetNotificationsEnabled(chatID string, enabled bool) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`UPDATE groups SET notifications_enabled = ?, last_updated = ? WHERE chat_id = ?`,
		enabled, time.Now().Format(time.RFC3339), chatID)
	if err != nil {
		logger.Errorf("[DB] SetNotificationsEnabled error: %v", err)
		return err
	}
	delete(d.settingsCache, chatID)
	return nil
}

func (d *DB) SetNotificationTime(chatID, timeStr string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`UPDATE groups SET notification_time = ?, last_updated = ? WHERE chat_id = ?`,
		timeStr, time.Now().Format(time.RFC3339), chatID)
	if err != nil {
		logger.Errorf("[DB] SetNotificationTime error: %v", err)
		return err
	}
	delete(d.settingsCache, chatID)
	return nil
}

func (d *DB) GetAllGroups() map[string]*GroupSettings {
	d.mu.Lock()
	defer d.mu.Unlock()

	rows, err := d.db.Query(`SELECT chat_id, chat_name, notifications_enabled, notification_time, timezone, last_updated FROM groups`)
	if err != nil {
		logger.Errorf("[DB] GetAllGroups error: %v", err)
		return make(map[string]*GroupSettings)
	}
	defer rows.Close()

	result := make(map[string]*GroupSettings)
	for rows.Next() {
		s := new(GroupSettings)
		if err := rows.Scan(&s.ChatID, &s.ChatName, &s.NotificationsEnabled, &s.NotificationTime, &s.Timezone, &s.LastUpdated); err != nil {
			logger.Errorf("[DB] GetAllGroups scan error: %v", err)
			continue
		}
		result[s.ChatID] = s
		d.settingsCache[s.ChatID] = s
	}

	return result
}

func (d *DB) GetGroupsWithNotifications() []string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT chat_id, notifications_enabled FROM groups`)
	if err != nil {
		logger.Errorf("[DB] GetGroupsWithNotifications error: %v", err)
		return nil
	}
	defer rows.Close()

	var result []string
	for rows.Next() {
		var chatID string
		var enabled int
		if err := rows.Scan(&chatID, &enabled); err != nil {
			logger.Errorf("[DB] GetGroupsWithNotifications scan error: %v", err)
			continue
		}
		if enabled == 1 {
			result = append(result, chatID)
		}
	}

	return result
}

func (d *DB) GetStatistics() map[string]interface{} {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var total, enabled int64
	d.db.QueryRow(`SELECT COUNT(*), SUM(notifications_enabled) FROM groups`).Scan(&total, &enabled)

	return map[string]interface{}{
		"total_groups":                total,
		"groups_with_notifications":   enabled,
		"groups_without_notifications": total - enabled,
		"last_updated":                 time.Now().Format(time.RFC3339),
	}
}

func (d *DB) AddBirthday(chatID, name string, day, month, year int) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT INTO birthdays (chat_id, name, day, month, year) VALUES (?, ?, ?, ?, ?)`,
		chatID, name, day, month, year)
	if err != nil {
		if strings.Contains(err.Error(), "UNIQUE") {
			return false
		}
		logger.Errorf("[DB] AddBirthday error: %v", err)
		return false
	}

	return true
}

func (d *DB) RemoveBirthday(chatID, name string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	result, err := d.db.Exec(`DELETE FROM birthdays WHERE chat_id = ? AND LOWER(name) = LOWER(?)`, chatID, name)
	if err != nil {
		return false
	}

	affected, _ := result.RowsAffected()
	return affected > 0
}

func (d *DB) GetBirthdaysForGroup(chatID string) map[string]Birthday {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT id, name, day, month, year FROM birthdays WHERE chat_id = ?`, chatID)
	if err != nil {
		return make(map[string]Birthday)
	}
	defer rows.Close()

	result := make(map[string]Birthday)
	for rows.Next() {
		var b Birthday
		if err := rows.Scan(&b.ID, &b.Name, &b.Day, &b.Month, &b.Year); err != nil {
			logger.Errorf("[DB] GetBirthdays scan error: %v", err)
			continue
		}
		key := strings.ToLower(b.Name)
		result[key] = b
	}

	return result
}

func (d *DB) AddWedding(chatID, name string, day, month, year int) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT INTO weddings (chat_id, name, day, month, year) VALUES (?, ?, ?, ?, ?)`,
		chatID, name, day, month, year)
	if err != nil {
		if strings.Contains(err.Error(), "UNIQUE") {
			return false
		}
		logger.Errorf("[DB] AddWedding error: %v", err)
		return false
	}

	return true
}

func (d *DB) RemoveWedding(chatID, name string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	result, err := d.db.Exec(`DELETE FROM weddings WHERE chat_id = ? AND LOWER(name) = LOWER(?)`, chatID, name)
	if err != nil {
		return false
	}

	affected, _ := result.RowsAffected()
	return affected > 0
}

func (d *DB) GetWeddingsForGroup(chatID string) map[string]Wedding {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT id, name, day, month, year FROM weddings WHERE chat_id = ?`, chatID)
	if err != nil {
		return make(map[string]Wedding)
	}
	defer rows.Close()

	result := make(map[string]Wedding)
	for rows.Next() {
		var w Wedding
		if err := rows.Scan(&w.ID, &w.Name, &w.Day, &w.Month, &w.Year); err != nil {
			logger.Errorf("[DB] GetWeddings scan error: %v", err)
			continue
		}
		key := strings.ToLower(w.Name)
		result[key] = w
	}

	return result
}

func (d *DB) UpdateEvent(chatID, oldName, newName, eventType, timeStr, text string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	if !strings.EqualFold(oldName, newName) {
		_, err := d.db.Exec(`DELETE FROM events WHERE chat_id = ? AND LOWER(name) = LOWER(?)`, chatID, oldName)
		if err != nil {
			logger.Errorf("[DB] UpdateEvent delete error: %v", err)
			return false
		}
	}
	_, err := d.db.Exec(`INSERT OR REPLACE INTO events (chat_id, name, type, time, text) VALUES (?, ?, ?, ?, ?)`,
		chatID, newName, eventType, timeStr, text)
	if err != nil {
		logger.Errorf("[DB] UpdateEvent error: %v", err)
		return false
	}
	return true
}

func (d *DB) AddEvent(chatID, name, eventType, timeStr, text string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT INTO events (chat_id, name, type, time, text) VALUES (?, ?, ?, ?, ?)`,
		chatID, name, eventType, timeStr, text)
	if err != nil {
		if strings.Contains(err.Error(), "UNIQUE") {
			return false
		}
		logger.Errorf("[DB] AddEvent error: %v", err)
		return false
	}
	return true
}

func (d *DB) RemoveEvent(chatID, name string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	result, err := d.db.Exec(`DELETE FROM events WHERE chat_id = ? AND LOWER(name) = LOWER(?)`, chatID, name)
	if err != nil {
		return false
	}

	affected, _ := result.RowsAffected()
	return affected > 0
}

func (d *DB) GetEventsForGroup(chatID string) map[string]Event {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT id, name, type, time, text FROM events WHERE chat_id = ?`, chatID)
	if err != nil {
		return make(map[string]Event)
	}
	defer rows.Close()

	result := make(map[string]Event)
	for rows.Next() {
		var e Event
		if err := rows.Scan(&e.ID, &e.Name, &e.Type, &e.Time, &e.Text); err != nil {
			logger.Errorf("[DB] GetEvents scan error: %v", err)
			continue
		}
		key := strings.ToLower(e.Name)
		result[key] = e
	}

	return result
}

func (d *DB) IsNotificationsEnabled(chatID string) bool {
	settings := d.GetGroupSettings(chatID)
	return settings.NotificationsEnabled
}

func (d *DB) GetNotificationTime(chatID string) string {
	settings := d.GetGroupSettings(chatID)
	return settings.NotificationTime
}

func (d *DB) GetAllCongratulations() []string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT text FROM congratulations WHERE is_active = 1`)
	if err != nil {
		logger.Errorf("[DB] GetAllCongratulations error: %v", err)
		return nil
	}
	defer rows.Close()

	var result []string
	for rows.Next() {
		var text string
		if err := rows.Scan(&text); err != nil {
			logger.Errorf("[DB] GetAllCongratulations scan error: %v", err)
			continue
		}
		result = append(result, text)
	}
	return result
}

func (d *DB) GetAllWeddingWishes() []string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(`SELECT text FROM wedding_wishes WHERE is_active = 1`)
	if err != nil {
		logger.Errorf("[DB] GetAllWeddingWishes error: %v", err)
		return nil
	}
	defer rows.Close()

	var result []string
	for rows.Next() {
		var text string
		if err := rows.Scan(&text); err != nil {
			logger.Errorf("[DB] GetAllWeddingWishes scan error: %v", err)
			continue
		}
		result = append(result, text)
	}
	return result
}

func (d *DB) AddCongratulations(text string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT INTO congratulations (text) VALUES (?)`, text)
	return err
}

func (d *DB) AddWeddingWish(text string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT INTO wedding_wishes (text) VALUES (?)`, text)
	return err
}

func (d *DB) RemoveCongratulations(text string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	res, err := d.db.Exec(`DELETE FROM congratulations WHERE text = ? AND is_active = 1`, text)
	if err != nil {
		logger.Errorf("[DB] RemoveCongratulations error: %v", err)
		return false
	}
	affected, _ := res.RowsAffected()
	return affected > 0
}

func (d *DB) RemoveWeddingWish(text string) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	res, err := d.db.Exec(`DELETE FROM wedding_wishes WHERE text = ? AND is_active = 1`, text)
	if err != nil {
		logger.Errorf("[DB] RemoveWeddingWish error: %v", err)
		return false
	}
	affected, _ := res.RowsAffected()
	return affected > 0
}

func (d *DB) GetCongratulationsCount() int {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var count int
	d.db.QueryRow(`SELECT COUNT(*) FROM congratulations WHERE is_active = 1`).Scan(&count)
	return count
}

func (d *DB) GetWeddingWishesCount() int {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var count int
	d.db.QueryRow(`SELECT COUNT(*) FROM wedding_wishes WHERE is_active = 1`).Scan(&count)
	return count
}

func (d *DB) SeedWishesFromJSON(congratulations []string, weddingWishes []string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	for _, text := range congratulations {
		d.db.Exec(`INSERT OR IGNORE INTO congratulations (text) VALUES (?)`, text)
	}

	for _, text := range weddingWishes {
		d.db.Exec(`INSERT OR IGNORE INTO wedding_wishes (text) VALUES (?)`, text)
	}

	return nil
}

func (d *DB) GetAllEventTemplates() map[string]string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	result := make(map[string]string)
	rows, err := d.db.Query(`SELECT key, text FROM event_templates`)
	if err != nil {
		return result
	}
	defer rows.Close()

	for rows.Next() {
		var key, text string
		if err := rows.Scan(&key, &text); err != nil {
			logger.Errorf("[DB] GetAllEventTemplates scan error: %v", err)
			continue
		}
		result[key] = text
	}
	return result
}

func (d *DB) UpdateEventTemplate(oldKey, newKey, text string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if oldKey != "" && !strings.EqualFold(oldKey, newKey) {
		_, err := d.db.Exec(`DELETE FROM event_templates WHERE key = ?`, oldKey)
		if err != nil {
			return err
		}
	}
	_, err := d.db.Exec(`INSERT OR REPLACE INTO event_templates (key, text) VALUES (?, ?)`, newKey, text)
	return err
}

func (d *DB) AddEventTemplate(key, text string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`INSERT OR REPLACE INTO event_templates (key, text) VALUES (?, ?)`, key, text)
	return err
}

func (d *DB) RemoveEventTemplate(key string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(`DELETE FROM event_templates WHERE key = ?`, key)
	return err
}