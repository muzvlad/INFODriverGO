package server

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"os/exec"
	"strings"
	"time"

	"infodriver/logger"
	"infodriver/storage"
)

type Server struct {
	db                 *storage.DB
	port               string
	token              string
	guiPath            string
	mux                *http.ServeMux
	server             *http.Server
	onTemplatesChanged func()
	onEventsChanged    func(chatID string)
}

type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func NewServer(db *storage.DB, port, token, guiPath string) *Server {
	return &Server{
		db:      db,
		port:    port,
		token:   token,
		guiPath: guiPath,
		mux:     http.NewServeMux(),
	}
}

func (s *Server) SetOnTemplatesChanged(fn func()) {
	s.onTemplatesChanged = fn
}

func (s *Server) Shutdown(ctx context.Context) error {
	if s.server != nil {
		return s.server.Shutdown(ctx)
	}
	return nil
}

func (s *Server) SetOnEventsChanged(fn func(chatID string)) {
	s.onEventsChanged = fn
}

func (s *Server) Start() error {
	s.setupRoutes()

	fs := http.FileServer(http.Dir(s.guiPath))
	s.mux.Handle("/gui/", http.StripPrefix("/gui/", fs))

	s.server = &http.Server{
		Addr:         ":" + s.port,
		Handler:      s.mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	logger.Infof("[SERVER] Starting API server on port %s", s.port)
	logger.Infof("[SERVER] Admin panel: http://0.0.0.0:%s/gui/", s.port)
	return s.server.ListenAndServe()
}

func (s *Server) setupRoutes() {
	s.mux.HandleFunc("/api/groups", s.corsMiddleware(s.handleGroups))
	s.mux.HandleFunc("/api/groups/", s.corsMiddleware(s.handleGroupDetail))
	s.mux.HandleFunc("/api/birthdays", s.corsMiddleware(s.handleBirthdays))
	s.mux.HandleFunc("/api/weddings", s.corsMiddleware(s.handleWeddings))
	s.mux.HandleFunc("/api/congratulations", s.corsMiddleware(s.handleCongratulations))
	s.mux.HandleFunc("/api/wishes", s.corsMiddleware(s.handleWishes))
	s.mux.HandleFunc("/api/events", s.corsMiddleware(s.handleEvents))
	s.mux.HandleFunc("/api/event-templates", s.corsMiddleware(s.handleEventTemplates))
	s.mux.HandleFunc("/api/run-tests", s.corsMiddleware(s.handleRunTests))
	s.mux.HandleFunc("/api/stats", s.corsMiddleware(s.handleStats))
	s.mux.HandleFunc("/health", s.corsMiddleware(s.handleHealth))
}

func (s *Server) corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

func (s *Server) authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			s.sendError(w, http.StatusUnauthorized, "No token provided")
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token != s.token {
			s.sendError(w, http.StatusUnauthorized, "Invalid token")
			return
		}

		next(w, r)
	}
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (s *Server) handleGroups(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			groupsMap := s.db.GetAllGroups()
			groups := make([]interface{}, 0, len(groupsMap))
			for _, g := range groupsMap {
				groups = append(groups, g)
			}
			s.sendSuccess(w, groups)
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleGroupDetail(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		id := strings.TrimPrefix(r.URL.Path, "/api/groups/")
		if id == "" {
			s.sendError(w, http.StatusBadRequest, "Group ID required")
			return
		}

		switch r.Method {
		case http.MethodGet:
			settings := s.db.GetGroupSettings(id)
			birthdays := s.db.GetBirthdaysForGroup(id)
			weddings := s.db.GetWeddingsForGroup(id)
			events := s.db.GetEventsForGroup(id)

			s.sendSuccess(w, map[string]interface{}{
				"settings":  settings,
				"birthdays": birthdays,
				"weddings":  weddings,
				"events":    events,
			})
		case http.MethodPut:
			var data map[string]interface{}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if notifications, ok := data["notifications_enabled"].(bool); ok {
				s.db.SetNotificationsEnabled(id, notifications)
			}
			if time, ok := data["notification_time"].(string); ok {
				s.db.SetNotificationTime(id, time)
			}

			if s.onEventsChanged != nil {
				go s.onEventsChanged(id)
			}

			s.sendSuccess(w, map[string]string{"status": "updated"})
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleBirthdays(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		chatID := r.URL.Query().Get("chat_id")
		if chatID == "" {
			s.sendError(w, http.StatusBadRequest, "chat_id required")
			return
		}

		switch r.Method {
		case http.MethodGet:
			birthdays := s.db.GetBirthdaysForGroup(chatID)
			s.sendSuccess(w, birthdays)
		case http.MethodPost:
			var data struct {
				Name  string `json:"name"`
				Day   int    `json:"day"`
				Month int    `json:"month"`
				Year  int    `json:"year"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if data.Name == "" || data.Day == 0 || data.Month == 0 {
				s.sendError(w, http.StatusBadRequest, "name, day, month required")
				return
			}

			ok := s.db.AddBirthday(chatID, data.Name, data.Day, data.Month, data.Year)
			if ok {
				s.sendSuccess(w, map[string]string{"status": "added"})
			} else {
				s.sendError(w, http.StatusConflict, "Birthday already exists")
			}
		case http.MethodDelete:
			name := r.URL.Query().Get("name")
			if name == "" {
				s.sendError(w, http.StatusBadRequest, "name required")
				return
			}

			ok := s.db.RemoveBirthday(chatID, name)
			if ok {
				s.sendSuccess(w, map[string]string{"status": "deleted"})
			} else {
				s.sendError(w, http.StatusNotFound, "Birthday not found")
			}
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleWeddings(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		chatID := r.URL.Query().Get("chat_id")
		if chatID == "" {
			s.sendError(w, http.StatusBadRequest, "chat_id required")
			return
		}

		switch r.Method {
		case http.MethodGet:
			weddings := s.db.GetWeddingsForGroup(chatID)
			s.sendSuccess(w, weddings)
		case http.MethodPost:
			var data struct {
				Name  string `json:"name"`
				Day   int    `json:"day"`
				Month int    `json:"month"`
				Year  int    `json:"year"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			ok := s.db.AddWedding(chatID, data.Name, data.Day, data.Month, data.Year)
			if ok {
				s.sendSuccess(w, map[string]string{"status": "added"})
			} else {
				s.sendError(w, http.StatusConflict, "Wedding already exists")
			}
		case http.MethodDelete:
			name := r.URL.Query().Get("name")
			if name == "" {
				s.sendError(w, http.StatusBadRequest, "name required")
				return
			}

			ok := s.db.RemoveWedding(chatID, name)
			if ok {
				s.sendSuccess(w, map[string]string{"status": "deleted"})
			} else {
				s.sendError(w, http.StatusNotFound, "Wedding not found")
			}
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleEvents(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		chatID := r.URL.Query().Get("chat_id")
		if chatID == "" {
			s.sendError(w, http.StatusBadRequest, "chat_id required")
			return
		}

		switch r.Method {
		case http.MethodGet:
			events := s.db.GetEventsForGroup(chatID)
			s.sendSuccess(w, events)
		case http.MethodPost:
			var data struct {
				Name string `json:"name"`
				Type string `json:"type"`
				Time string `json:"time"`
				Text string `json:"text"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if data.Name == "" || data.Type == "" || data.Time == "" {
				s.sendError(w, http.StatusBadRequest, "name, type, time required")
				return
			}

			ok := s.db.AddEvent(chatID, data.Name, data.Type, data.Time, data.Text)
			if ok {
				if s.onEventsChanged != nil {
					go s.onEventsChanged(chatID)
				}
				s.sendSuccess(w, map[string]string{"status": "added"})
			} else {
				s.sendError(w, http.StatusConflict, "Event already exists")
			}
		case http.MethodDelete:
			name := r.URL.Query().Get("name")
			if name == "" {
				s.sendError(w, http.StatusBadRequest, "name required")
				return
			}

			ok := s.db.RemoveEvent(chatID, name)
			if ok {
				if s.onEventsChanged != nil {
					go s.onEventsChanged(chatID)
				}
				s.sendSuccess(w, map[string]string{"status": "deleted"})
			} else {
				s.sendError(w, http.StatusNotFound, "Event not found")
			}
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleEventTemplates(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			templates := s.db.GetAllEventTemplates()
			s.sendSuccess(w, templates)
		case http.MethodPost:
			var data struct {
				Key  string `json:"key"`
				Text string `json:"text"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if data.Key == "" || data.Text == "" {
				s.sendError(w, http.StatusBadRequest, "key and text required")
				return
			}

			err := s.db.AddEventTemplate(strings.ToLower(data.Key), data.Text)
			if err != nil {
				s.sendError(w, http.StatusInternalServerError, err.Error())
				return
			}

			if s.onTemplatesChanged != nil {
				go s.onTemplatesChanged()
			}

			s.sendSuccess(w, map[string]string{"status": "saved"})
		case http.MethodDelete:
			key := r.URL.Query().Get("key")
			if key == "" {
				s.sendError(w, http.StatusBadRequest, "key required")
				return
			}

			err := s.db.RemoveEventTemplate(key)
			if err != nil {
				s.sendError(w, http.StatusInternalServerError, err.Error())
				return
			}

			if s.onTemplatesChanged != nil {
				s.onTemplatesChanged()
			}

			s.sendSuccess(w, map[string]string{"status": "deleted"})
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleCongratulations(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			texts := s.db.GetAllCongratulations()
			s.sendSuccess(w, texts)
		case http.MethodPost:
			var data struct {
				Text string `json:"text"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if data.Text == "" {
				s.sendError(w, http.StatusBadRequest, "text required")
				return
			}

			s.db.AddCongratulations(data.Text)
			s.sendSuccess(w, map[string]string{"status": "added"})
		case http.MethodDelete:
			text := r.URL.Query().Get("text")
			if text == "" {
				s.sendError(w, http.StatusBadRequest, "text required")
				return
			}

			ok := s.db.RemoveCongratulations(text)
			if ok {
				s.sendSuccess(w, map[string]string{"status": "deleted"})
			} else {
				s.sendError(w, http.StatusNotFound, "Text not found")
			}
		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleWishes(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		wishType := r.URL.Query().Get("type")

		switch r.Method {
		case http.MethodGet:
			result := make(map[string]interface{})
			if wishType == "" || wishType == "congratulations" {
				result["congratulations"] = s.db.GetAllCongratulations()
			}
			if wishType == "" || wishType == "wedding" {
				result["weddings"] = s.db.GetAllWeddingWishes()
			}
			s.sendSuccess(w, result)

		case http.MethodPost:
			var data struct {
				Text string `json:"text"`
			}
			if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
				s.sendError(w, http.StatusBadRequest, "Invalid JSON")
				return
			}

			if data.Text == "" {
				s.sendError(w, http.StatusBadRequest, "text required")
				return
			}

			switch wishType {
			case "wedding":
				s.db.AddWeddingWish(data.Text)
			default:
				s.db.AddCongratulations(data.Text)
			}
			s.sendSuccess(w, map[string]string{"status": "added"})

		case http.MethodDelete:
			text := r.URL.Query().Get("text")
			if text == "" {
				s.sendError(w, http.StatusBadRequest, "text required")
				return
			}

			var ok bool
			switch wishType {
			case "wedding":
				ok = s.db.RemoveWeddingWish(text)
			default:
				ok = s.db.RemoveCongratulations(text)
			}

			if ok {
				s.sendSuccess(w, map[string]string{"status": "deleted"})
			} else {
				s.sendError(w, http.StatusNotFound, "Text not found")
			}

		default:
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
		}
	})(w, r)
}

func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		stats := s.db.GetStatistics()

		allGroups := s.db.GetAllGroups()
		totalBD := 0
		totalWed := 0
		totalEvents := 0

		for _, g := range allGroups {
			bds := s.db.GetBirthdaysForGroup(g.ChatID)
			weds := s.db.GetWeddingsForGroup(g.ChatID)
			evts := s.db.GetEventsForGroup(g.ChatID)
			totalBD += len(bds)
			totalWed += len(weds)
			totalEvents += len(evts)
		}

		stats["total_birthdays"] = totalBD
		stats["total_weddings"] = totalWed
		stats["total_events"] = totalEvents
		stats["congratulations_count"] = s.db.GetCongratulationsCount()
		stats["wedding_wishes_count"] = s.db.GetWeddingWishesCount()

		s.sendSuccess(w, stats)
	})(w, r)
}

func (s *Server) handleRunTests(w http.ResponseWriter, r *http.Request) {
	s.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			s.sendError(w, http.StatusMethodNotAllowed, "Method not allowed")
			return
		}

		results := make(map[string]interface{})

		// Unit tests (bot)
		unitOut, unitErr := runGoTest("./bot/...")
		results["unit"] = map[string]interface{}{
			"output":  unitOut,
			"success": unitErr == nil,
		}

		// Integration tests (tests/)
		integOut, integErr := runGoTest("./tests/...")
		results["integration"] = map[string]interface{}{
			"output":  integOut,
			"success": integErr == nil,
		}

		s.sendSuccess(w, results)
	})(w, r)
}

func runGoTest(pkg string) (string, error) {
	cmd := exec.Command("go", "test", "-v", "-count=1", pkg)
	var out bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	return out.String(), err
}

func (s *Server) sendSuccess(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(APIResponse{Success: true, Data: data})
}

func (s *Server) sendError(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(APIResponse{Success: false, Error: message})
}
