#!/bin/bash

# VibeLearn仓库每日自动同步脚本
# 每天凌晨00:01自动将最新代码推送到GitHub

LOG_FILE="/workspace/sync.log"
REPO_PATH="/workspace"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

cd "$REPO_PATH" || {
    log "ERROR: 无法进入仓库目录 $REPO_PATH"
    exit 1
}

log "========== 开始每日同步 =========="
log "仓库路径: $REPO_PATH"

# 检查Git用户配置
if ! git config user.email >/dev/null 2>&1 || ! git config user.name >/dev/null 2>&1; then
    log "WARNING: Git用户未配置，尝试自动配置..."
    git config user.email "ci-auto-sync@vibelearn.local"
    git config user.name "VibeLearn Auto Sync"
fi

# 拉取最新代码
log "执行 git pull origin main..."
if git pull origin main 2>&1 | tee -a "$LOG_FILE"; then
    log "代码拉取成功"
else
    log "WARNING: git pull 失败或没有远程更新"
fi

# 检查是否有本地修改
log "检查本地修改状态..."
git_status=$(git status --porcelain)

if [ -z "$git_status" ]; then
    log "没有本地修改，无需推送"
    log "========== 同步完成 =========="
    exit 0
fi

log "检测到本地修改，准备提交..."

# 暂存所有更改
log "执行 git add ."
git add . 2>&1 | tee -a "$LOG_FILE"

# 生成提交信息
commit_msg="Daily sync: $(date "+%Y-%m-%d %H:%M")"

log "执行 git commit -m \"$commit_msg\""
git commit -m "$commit_msg" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    log "ERROR: git commit 失败"
    exit 1
fi
log "提交成功"

# 推送到远程
log "执行 git push origin main"
if git push origin main 2>&1 | tee -a "$LOG_FILE"; then
    log "推送成功"
else
    log "ERROR: git push 失败"
    exit 1
fi

log "========== 同步完成 =========="
exit 0
