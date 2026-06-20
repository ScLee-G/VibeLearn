#!/bin/bash

# 停止VibeLearn每日同步守护进程

PID_FILE="/workspace/sync_daemon.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "守护进程未运行"
    exit 0
fi

pid=$(cat "$PID_FILE")
if ps -p "$pid" > /dev/null 2>&1; then
    kill "$pid"
    echo "守护进程已停止 (PID: $pid)"
else
    echo "守护进程未运行"
fi

rm -f "$PID_FILE"
