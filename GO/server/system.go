package server

import (
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type SystemStats struct {
	CPUUsage     float64 `json:"cpu_usage"`
	MemoryTotal  uint64  `json:"memory_total"`
	MemoryUsed   uint64  `json:"memory_used"`
	MemoryPct    float64 `json:"memory_pct"`
	GoVersion    string  `json:"go_version"`
	NumCPU       int     `json:"num_cpu"`
	NumGoroutine int     `json:"num_goroutine"`
	Uptime       string  `json:"uptime"`
}

func GetSystemStats() *SystemStats {
	s := &SystemStats{
		GoVersion:    runtime.Version(),
		NumCPU:       runtime.NumCPU(),
		NumGoroutine: runtime.NumGoroutine(),
		Uptime:       getUptime(),
	}

	if cpu, err := getCPUUsage(); err == nil {
		s.CPUUsage = cpu
	}
	if memTotal, memUsed, err := getMemoryUsage(); err == nil {
		s.MemoryTotal = memTotal
		s.MemoryUsed = memUsed
		if memTotal > 0 {
			s.MemoryPct = float64(memUsed) / float64(memTotal) * 100
		}
	}

	return s
}

func readProcFile(path string) ([]byte, error) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil, err
	}
	return os.ReadFile(path)
}

func getCPUUsage() (float64, error) {
	data, err := readProcFile("/proc/stat")
	if err != nil {
		return 0, err
	}

	line := getFirstLine(data, "cpu ")
	if line == "" {
		return 0, nil
	}
	idle1, total1 := parseCPUTimes(line)

	time.Sleep(500 * time.Millisecond)

	data2, err := readProcFile("/proc/stat")
	if err != nil {
		return 0, err
	}

	line2 := getFirstLine(data2, "cpu ")
	if line2 == "" {
		return 0, nil
	}
	idle2, total2 := parseCPUTimes(line2)

	idleDelta := idle2 - idle1
	totalDelta := total2 - total1
	if totalDelta == 0 {
		return 0, nil
	}

	return float64(totalDelta-idleDelta) / float64(totalDelta) * 100, nil
}

func getFirstLine(data []byte, prefix string) string {
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, prefix) {
			return line
		}
	}
	return ""
}

func parseCPUTimes(line string) (idle, total uint64) {
	fields := strings.Fields(line)
	if len(fields) < 5 {
		return 0, 0
	}

	for i, f := range fields {
		if i == 0 {
			continue
		}
		val, _ := strconv.ParseUint(f, 10, 64)
		total += val
		if i == 4 {
			idle = val
		}
	}
	return
}

func getMemoryUsage() (total, used uint64, err error) {
	data, err := readProcFile("/proc/meminfo")
	if err != nil {
		return 0, 0, err
	}

	lines := strings.Split(string(data), "\n")
	var memTotal, memAvail uint64

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "MemTotal:") {
			memTotal = parseMemValue(line)
		} else if strings.HasPrefix(line, "MemAvailable:") {
			memAvail = parseMemValue(line)
		}
	}

	if memTotal == 0 {
		return 0, 0, nil
	}

	return memTotal, memTotal - memAvail, nil
}

func parseMemValue(line string) uint64 {
	fields := strings.Fields(line)
	if len(fields) < 2 {
		return 0
	}
	val, _ := strconv.ParseUint(fields[1], 10, 64)
	return val
}

func getUptime() string {
	data, err := readProcFile("/proc/uptime")
	if err != nil {
		return ""
	}

	fields := strings.Fields(string(data))
	if len(fields) == 0 {
		return ""
	}

	seconds, _ := strconv.ParseFloat(fields[0], 64)
	uptime := time.Duration(seconds) * time.Second

	days := int(uptime.Hours()) / 24
	hours := int(uptime.Hours()) % 24
	minutes := int(uptime.Minutes()) % 60

	if days > 0 {
		return formatDuration(days, hours, minutes)
	}
	return formatDuration(0, hours, minutes)
}

func formatDuration(days, hours, minutes int) string {
	if days > 0 {
		return strconv.Itoa(days) + "д " + strconv.Itoa(hours) + "ч " + strconv.Itoa(minutes) + "м"
	}
	return strconv.Itoa(hours) + "ч " + strconv.Itoa(minutes) + "м"
}
