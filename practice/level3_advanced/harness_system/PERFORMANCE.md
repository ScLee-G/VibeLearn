# Harness 系统性能优化指南

本指南介绍如何配置和优化 Harness 系统以获得最佳性能。

## 最低系统要求

### 最小配置:
- CPU: 2 核心
- 内存: 4 GB RAM
- 磁盘: 500 MB 可用空间
- Python 网络: 稳定的互联网连接

### 推荐配置:
- CPU: 4+ 核心
- 内存: 8+ GB RAM
- 磁盘: 2+ GB 可用空间
- 网络: 高速互联网连接

## 性能配置选项

### 命令行配置

```bash
# 禁用资源监控（减少开销
python run_harness.py --no-resource-monitor "任务描述"

# 自定义资源阈值
python run_harness.py --max-memory 85.0 --max-cpu 90.0 "任务描述"

# 缩短超时时间
python run_harness.py --timeout 180 "任务描述"
```

### Python API 配置

```python
controller = HarnessController(
    project_path="./my_project",
    project_name="我的项目",
    llm_client=client,
    
    # 资源监控控制
    enable_resource_monitoring=True,        # 启用监控 (推荐保留)
    max_cpu_percent=95.0,                 # CPU 上限百分比
    max_memory_percent=90.0,               # 内存上限百分比
    max_disk_percent=95.0,                 # 磁盘上限百分比
    
    # 超时控制
    feature_timeout_seconds=300,                  # 功能超时时间 (秒)
)
```

## 优化策略

### 1. 内存优化

**问题**: 内存使用过高

**解决方案**:
- 增加 `--max-memory` 设置，提高上限（需要确保其他占用）
- 禁用不必要的资源监控 `--no-resource-monitor`
- 使用更小的缓存大小
- 定期清理临时文件

```python
# 清理临时文件
from harness_system.resource_manager import ResourceOptimizer

optimizer = ResourceOptimizer()
clean_result = optimizer.clean_temporary_files("./projects/temp", age_hours=12)
print(f"清理了 {clean_result['items_removed']} 个文件，释放 {clean_result['space_freed_mb']:.1f} MB")
```

### 2. CPU 优化

**问题**: CPU 使用过高导致响应慢

**解决方案**:
- 限制 `--max-cpu` 阈值，控制上限
- 在 Sprints 间的时间间隔
- 使用更优批处理小的策略

### 3. 响应时间优化

使用缓存

```python
# 响应缓存默认启用，TTLCache
from harness_system import SimpleCache

# 增加缓存大小
cache = SimpleCache(max_size=100, ttl_seconds=3600)  # 1小时

# 手动管理缓存
controller.clear_cache()  # 清空
```

## 性能监控

运行 Harness 后会自动收集性能数据

查看性能报告：

```python
# 交互模式
>>> performance

# Python API
report = controller.get_performance_report()
print(f"总耗时: {report['current']['total_duration_seconds']:.1f}秒")
print(f"缓存命中率: {report.get('cache_size')}")
```

## 故障排除

### 内存使用高峰时会出现警告如遇到资源警告

```bash
# 禁用资源监控运行
python run_harness.py --no-resource-monitor "任务描述"

# 或者提高资源阈值调整
python run_harness.py --max-memory 95.0 --max-cpu 100.0 "任务描述"
```

### 任务卡住问题处理

```python
# 缩短超时时间
controller = HarnessController(
    ...,
    feature_timeout_seconds=180  # 3分钟而不是5分钟
)
```

## 高级优化配置推荐不同任务的处理

### 小项目小任务 (<10功能):
```bash
# 不需要太严格的监控
python run_harness.py --max-cpu 98.0 --timeout 120 "简单任务"
```

### 大型项目 (>20功能):
```bash
# 更严格资源监控（默认即可）
python run_harness.py --timeout 600 "大型项目"
```

## 查看性能数据文件生成路径

所有数据都保存项目的 `.harness` 目录下:
- `performance.json`: 性能指标
- `resource_logs/`: 资源使用快照
- `progress_log.json`: 操作日志
- `feature_list.json`: 功能列表

## 最佳实践

1. 关闭不需要资源监控下运行
2. 任务分批处理功能
3. 定期检查和分析运行时
4. 及时清理缓存和临时文件
5. 使用合适的模型选项配置

