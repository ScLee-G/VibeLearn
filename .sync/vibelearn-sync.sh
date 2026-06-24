#!/bin/bash
# VibeLearn Daily Sync Script
# 每天凌晨自动将最新代码推送到GitHub

LOG_FILE="/workspace/.sync/sync.log"
REPO_DIR="/workspace"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

cd "$REPO_DIR" || {
    log "ERROR: 无法进入仓库目录 $REPO_DIR"
    exit 1
}

log "========== 开始同步 =========="
log "当前分支: $(git branch --show-current)"
log "当前commit: $(git rev-parse --short HEAD)"

# 拉取最新代码
log "执行 git pull origin main..."
if ! git pull origin main >> "$LOG_FILE" 2>&1; then
    log "ERROR: git pull 失败"
    exit 1
fi

# 检查是否有本地修改
if [[ -n $(git status --porcelain) ]]; then
    log "检测到本地修改，开始提交..."

    # 暂存所有更改
    git add .

    # 生成提交信息
    COMMIT_MSG="Daily sync: $(date "+%Y-%m-%d %H:%M")"

    # 执行提交
    log "提交信息: $COMMIT_MSG"
    if ! git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1; then
        log "ERROR: git commit 失败"
        exit 1
    fi

    # 推送到远程
    log "执行 git push origin main..."
    if ! git push origin main >> "$LOG_FILE" 2>&1; then
        log "ERROR: git push 失败"
        exit 1
    fi

    log "同步完成并已推送"
else
    log "没有本地修改，无需推送"
fi

log "========== 同步结束 =========="
echo "" >> "$LOG_FILE"
