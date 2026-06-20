#!/bin/bash

# 启动VibeLearn每日同步守护进程

DAEMON_SCRIPT="/workspace/sync_daemon.sh"
PID_FILE="/workspace/sync_daemon.pid"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "守护进程已在运行 (PID: $pid)"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动守护进程
echo "启动VibeLearn每日同步守护进程..."
nohup bash "$DAEMON_SCRIPT" > /dev/null 2>&1 &
pid=$!
echo $pid > "$PID_FILE"
echo "守护进程已启动 (PID: $pid)"
echo "日志文件: /workspace/sync.log"
