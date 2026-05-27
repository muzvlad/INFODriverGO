# INFODriverGO — Changelog

## v1.11 (current)
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
