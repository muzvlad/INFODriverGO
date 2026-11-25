#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import platform

print("=== ИНФОРМАЦИЯ О PYTHON ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python version info: {sys.version_info}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.architecture()}")

# Проверим, есть ли предупреждение о версии
try:
    import telegram
    print(f"Telegram bot version: {telegram.__version__}")
except ImportError as e:
    print(f"Import error: {e}")

print("=== ТЕСТ ЗАВЕРШЕН ===")