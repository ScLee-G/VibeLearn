#!/bin/bash

# VibeLearn仓库每日同步守护进程
# 后台运行，每天凌晨00:01执行同步

LOG_FILE="/workspace/sync.log"
REPO_PATH="/workspace"
SYNC_SCRIPT="/workspace/daily_sync.sh"

log() {
    echo "[$(date "+%Y-%m-%d %H:%M:%S")] [DAEMON] $1" | tee -a "$LOG_FILE"
}

log "守护进程启动"

while true; do
    # 获取当前时间
    current_hour=$(date +%H)
    current_minute=$(date +%M)

    # 检查是否是00:01
    if [ "$current_hour" = "00" ] && [ "$current_minute" = "01" ]; then
        log "触发每日同步任务"
        bash "$SYNC_SCRIPT"
        # 等待一分钟避免重复执行
        sleep 60
    fi

    # 每分钟检查一次
    sleep 60
done
