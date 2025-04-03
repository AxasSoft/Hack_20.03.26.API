#!/bin/bash

# Порог загрузки процессора
CPU_THRESHOLD=80

# Порог использования памяти
MEM_THRESHOLD=90

# Получение текущей загрузки процессора
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')

# Получение текущего использования памяти
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f"), $3/$2 * 100}')

# Проверка нагрузок и отправка уведомлений
if (( ${CPU_USAGE%.*} > CPU_THRESHOLD )); then
    notify-send "Внимание: Высокая загрузка CPU!" "Текущая загрузка: $CPU_USAGE%"
fi

if (( MEM_USAGE > MEM_THRESHOLD )); then
    notify-send "Внимание: Высокое использование памяти!" "Используется $MEM_USAGE% памяти."
fi

echo "Состояние системы проверено: CPU $CPU_USAGE%, RAM $MEM_USAGE%"
