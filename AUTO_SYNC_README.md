# VibeLearn 每日自动同步系统

## 功能说明

每天凌晨 00:01 自动将 VibeLearn 仓库的最新代码推送到 GitHub。

## 文件说明

- `daily_sync.sh` - 主同步脚本，执行 git pull、检查修改、提交和推送
- `sync_daemon.sh` - 后台守护进程，每分钟检查时间并在 00:01 触发同步
- `start_sync_daemon.sh` - 启动守护进程
- `stop_sync_daemon.sh` - 停止守护进程
- `sync.log` - 操作日志文件

## 使用方法

### 启动自动同步

```bash
/workspace/start_sync_daemon.sh
```

### 停止自动同步

```bash
/workspace/stop_sync_daemon.sh
```

### 手动执行同步

```bash
/workspace/daily_sync.sh
```

### 查看日志

```bash
tail -f /workspace/sync.log
```

### 检查守护进程状态

```bash
ps aux | grep sync_daemon | grep -v grep
```

## 工作流程

1. 守护进程每分钟检查当前时间
2. 当时间为 00:01 时，触发同步脚本
3. 同步脚本执行以下操作：
   - 进入工作目录 `/workspace`
   - 执行 `git pull origin main` 拉取最新代码
   - 检查是否有本地修改（`git status`）
   - 如果有修改：
     - 执行 `git add .` 暂存所有更改
     - 使用自动生成的提交信息执行 `git commit`
     - 执行 `git push origin main` 推送到远程
   - 如果没有修改，记录日志后结束

## 提交信息格式

```
Daily sync: YYYY-MM-DD HH:MM
```

例如：`Daily sync: 2026-06-20 00:01`

## 注意事项

- 确保 SSH token 配置正确，有推送权限
- 所有操作日志记录在 `/workspace/sync.log`
- 守护进程 PID 存储在 `/workspace/sync_daemon.pid`
- 如果系统重启，需要重新启动守护进程

## 开机自启动（可选）

如果需要在系统启动时自动启动守护进程，可以将以下内容添加到 `/etc/rc.local` 或用户的 shell 配置文件中：

```bash
/workspace/start_sync_daemon.sh
```

## 故障排查

### 查看守护进程是否运行

```bash
ps aux | grep sync_daemon
```

### 查看最近的同步日志

```bash
tail -50 /workspace/sync.log
```

### 手动测试同步脚本

```bash
bash /workspace/daily_sync.sh
```

### 检查 Git 配置

```bash
git config --list | grep user
```
