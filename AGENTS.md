# INFODriverGO — Changelog

## v1.13 (current)
- Fix data races: чтение `b.congratulations`/`b.weddings`/`b.events` теперь под `RLock`
- Fix reminder key mismatch: `SetupThreeDaysReminder` и `RemoveReminderJob` используют одинаковый формат ключа (с именем) — напоминания корректно удаляются при `/delete` и `/несвадьба`
- Fix events from admin panel: убран `go` из вызова `onEventsChanged`, добавлен `SetupAndCheckEvents` — джоб создаётся синхронно и сразу проверяется (без ожидания 30с цикла); добавлен `force`-параметр в `checkEventJobs` — при добавлении события grace period не применяется, событие триггерится немедленно
- Fix UpdateEvent: `INSERT OR REPLACE` вместо `INSERT` — редактирование без смены имени больше не падает на UNIQUE
- Fix getDaysUntil: DST-безопасное вычисление через `Hours()/24` вместо целочисленного деления `time.Duration`
- Fix main loop: добавлен `time.Sleep(5s)` и флаг `gracefulStop` — при краше не жжёт CPU
- Fix DB: `synchronous=FULL` → `NORMAL` (WAL + NORMAL в 10-100x быстрее на запись)
- Fix GetStatistics: один запрос `COUNT(*), SUM()` вместо двух
- Refactor: единая переменная `monthNames` в utils.go (убрано 4 дубликата)
- Config: `AdminUsername` читается из `ADMIN_USERNAME` env (с fallback)
- XSS: добавлена функция `esc()` в админке, экранирование пользовательских данных в HTML

## v1.12
- Remove dead code: internal/ (~650 строк), GO/groups/*.json, LoadAllGroups(), SendEventNotification(), rand.Seed(), SetupGroupJob/RemoveGroupJob, init() с log.SetFlags(0)
- Fix handleNoEvent: добавлен RemoveEventJob — событие удаляется и из памяти
- Fix AddEvent: INSERT OR REPLACE → INSERT + UNIQUE (как birthdays/weddings)
- Fix getDaysUntil: integer division вместо Hours()/24 (DST-безопасно)
- Remove recover() под Lock в scheduler.run() — deadlock при панике
- Graceful shutdown для HTTP-сервера (Shutdown с context.WithTimeout)
- Кэш GroupSettings (double-check locking, инвалидация при writes)
- Grace period 10 мин для reminder-джоб (как в checkEventJobs)
- Добавлен уровневый логгер (GO/logger/logger.go) с поддержкой LOG_LEVEL из .env
- Все log.Printf/log.Fatalf заменены на logger.Debugf/Infof/Warnf/Errorf/Fatalf
- GUI path — параметр NewServer(db, port, token, guiPath)
- Админка: добавлена вкладка «🧪 Тесты» с кнопкой запуска через /api/run-tests
- Тесты: unit-тесты (bot/utils, bot/scheduler), интеграционные (storage, logger)
- Скрипты: run_tests.bat (Windows), run_tests.sh (Linux)
- Fix: удалены захардкоженные массивы поздравлений из randomCongratulation/randomWeddingCongratulation — все поздравления только из БД
- Deploy: добавлен deploy.sh — git pull + установка infodriver_arm64 + restart
- Start: start_bot.sh теперь предпочитает pre-compiled ARM64 бинарник сборке из исходников
- API: PUT /api/event-templates (редактирование шаблона с old_key)
- API: PUT /api/events (редактирование события)
- GUI: выбор шаблона при добавлении события (dropdown)
- GUI: колонка Текст в списке событий, кнопка редактирования ✏️
- GUI: кнопка редактирования шаблона ✏️
- Fix: таймаут тестов 10с → 120с (abort без причины)
- GUI: выбор запуска тестов — на сервере или локально (с копированием команды)

## v1.11
- `calculateNextEventRun`: don't advance daily events to tomorrow — keeps `nextRun` on today
- `checkEventJobs`: 10-minute grace period — past events fire once then reschedule; older events just reschedule (no duplicate on restart)
- `run()`: call `checkJobs()` immediately after `loadEventJobs()` for catch-up on startup
- Logging: add date to `nextRun` log, fix per-group event count
- Fix: duplicate bot instances (systemd + manual `./start_bot.sh`) causing SQLite lock on writes — kill old processes before restart

## v1.10f
- Debug: log each event in `checkEventJobs`, merge trigger+reschedule under single Lock

## v1.10e
- Add debug log in `checkEventJobs`, merge trigger+reschedule under single Lock

## v1.09
- Fix events form: show/hide pre-built fields instead of innerHTML — buttons now work

## v1.08
- Events form: dynamic fields — date picker for одноразово, day-of-week dropdown for еженедельно, day-of-month dropdown for ежемесячно, time input for ежедневно
- Birthdays/Weddings: add date picker input

## v1.07
- Add AGENTS.md with changelog

## v1.06
- `UpdateGroupJobTime`: clear activeJobs on time change, send immediately if time passed
- Server: call scheduler callback on notification_time change from admin panel

## v1.05
- Add recover() in scheduler loop — panic won't kill goroutine
- More logging in checkDailyNotifications and checkEventJobs

## v1.04
- Fix scheduler deadlocks: collect triggered jobs under RLock, release, then Lock for reschedule
- Fix data races in checkReminderJobs (same collect-release-lock pattern)
- Fix getDaysUntil: today's birthdays now show in "Ближайшие"

## v1.03
- Fix events not firing from admin panel — add SetOnEventsChanged callback
- Wire scheduler.SetupEventJobs on API event add/delete

## v1.02
- Add MyChatMember handler — bot detects group add/remove on restart
- Fix GetGroupSettings deadlock (RLock→Lock)
- Fix UpdateGroupInfo not inserting new groups (UPDATE 0 rows)
- Fix GetAllGroups returning same struct for all entries (&s bug)
- Fix checkDailyRestart blocking on unbuffered channel
- Fix chat ID 0 send in Start()
- Pre-compiled ARM64 binary for Raspberry Pi
- GitHub release: https://github.com/muzvlad/INFODriverGO

## v1.01
- Initial commit: bot, scheduler, storage, server, GUI
