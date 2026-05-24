"""
Harness 系统 - 资源管理器

管理系统资源使用：
- 内存监控
- 磁盘空间检查
- CPU/GPU 负载监控
- 运行时性能优化
- 超时控制
- 缓存机制
"""

import os
import time
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class ResourceUsage:
    """资源使用快照"""
    timestamp: str
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    cpu_percent: float
    disk_used_mb: float
    disk_total_mb: float
    disk_percent: float
    active_processes: int


@dataclass
class PerformanceMetrics:
    """性能指标"""
    start_time: str
    end_time: str
    total_duration_seconds: float
    total_tokens_used: int
    total_api_calls: int
    avg_response_time_seconds: float
    features_completed: int
    total_features: int
    completion_rate: float


class ResourceMonitor:
    """资源监控器"""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = Path(log_path) if log_path else Path.cwd() / ".harness" / "resource_logs"
        self.log_path.mkdir(parents=True, exist_ok=True)
        self._snapshots: list[ResourceUsage] = []
        self._process = psutil.Process(os.getpid())

    def snapshot(self) -> ResourceUsage:
        """获取当前资源使用快照"""
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        snapshot = ResourceUsage(
            timestamp=datetime.now().isoformat(),
            memory_used_mb=mem.used / (1024 * 1024),
            memory_total_mb=mem.total / (1024 * 1024),
            memory_percent=mem.percent,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            disk_used_mb=disk.used / (1024 * 1024),
            disk_total_mb=disk.total / (1024 * 1024),
            disk_percent=disk.percent,
            active_processes=len(psutil.pids())
        )

        self._snapshots.append(snapshot)
        return snapshot

    def check_warnings(self, snapshot: Optional[ResourceUsage] = None) -> list[str]:
        """检查是否有资源警告"""
        snapshot = snapshot or self.snapshot()
        warnings = []

        if snapshot.memory_percent > 85:
            warnings.append(f"高内存使用: {snapshot.memory_percent:.1f}%")

        if snapshot.cpu_percent > 90:
            warnings.append(f"高 CPU 使用: {snapshot.cpu_percent:.1f}%")

        if snapshot.disk_percent > 90:
            warnings.append(f"低磁盘空间: {snapshot.disk_percent:.1f}%")

        return warnings

    def save_snapshot(self, snapshot: ResourceUsage):
        """保存快照到文件"""
        file_name = f"snapshot_{snapshot.timestamp.replace(':', '-')}.json"
        file_path = self.log_path / file_name

        with open(file_path, "w") as f:
            json.dump(asdict(snapshot), f, indent=2)

    def get_average_usage(self, last_n: int = 10) -> Dict[str, float]:
        """获取平均资源使用"""
        if not self._snapshots:
            return {}

        recent = self._snapshots[-last_n:]
        return {
            "avg_memory_percent": sum(s.memory_percent for s in recent) / len(recent),
            "avg_cpu_percent": sum(s.cpu_percent for s in recent) / len(recent),
            "avg_disk_percent": sum(s.disk_percent for s in recent) / len(recent),
            "samples": len(recent)
        }


class PerformanceTracker:
    """性能追踪器"""

    def __init__(self):
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._token_usage: int = 0
        self._api_calls: int = 0
        self._response_times: list[float] = []
        self._features_completed: int = 0
        self._total_features: int = 0
        self._checkpoints: Dict[str, float] = {}

    def start(self):
        """开始追踪"""
        self._start_time = time.time()

    def checkpoint(self, name: str):
        """记录检查点"""
        self._checkpoints[name] = time.time()

    def record_api_call(self, duration_seconds: float, tokens: int = 0):
        """记录 API 调用"""
        self._api_calls += 1
        self._token_usage += tokens
        self._response_times.append(duration_seconds)

    def record_feature_completion(self, completed: int, total: int):
        """记录功能完成"""
        self._features_completed = completed
        self._total_features = total

    def stop(self) -> PerformanceMetrics:
        """停止追踪并返回指标"""
        self._end_time = time.time()

        avg_response = 0.0
        if self._response_times:
            avg_response = sum(self._response_times) / len(self._response_times)

        completion_rate = 0.0
        if self._total_features > 0:
            completion_rate = self._features_completed / self._total_features

        return PerformanceMetrics(
            start_time=datetime.fromtimestamp(self._start_time).isoformat() if self._start_time else "",
            end_time=datetime.fromtimestamp(self._end_time).isoformat() if self._end_time else "",
            total_duration_seconds=self._end_time - self._start_time if self._start_time and self._end_time else 0,
            total_tokens_used=self._token_usage,
            total_api_calls=self._api_calls,
            avg_response_time_seconds=avg_response,
            features_completed=self._features_completed,
            total_features=self._total_features,
            completion_rate=completion_rate
        )


class TimeoutManager:
    """超时管理器"""

    def __init__(self, default_timeout_seconds: int = 300):
        self.default_timeout = default_timeout_seconds
        self._timeouts: Dict[str, float] = {}

    def set_timeout(self, name: str, seconds: float):
        """设置超时"""
        self._timeouts[name] = time.time() + seconds

    def check_timeout(self, name: str) -> bool:
        """检查是否超时"""
        if name not in self._timeouts:
            return False
        return time.time() > self._timeouts[name]

    def clear_timeout(self, name: str):
        """清除超时"""
        self._timeouts.pop(name, None)

    def run_with_timeout(self, func: Callable, timeout_seconds: int = None, *args, **kwargs):
        """带超时运行函数"""
        import concurrent.futures

        timeout = timeout_seconds or self.default_timeout

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"操作在 {timeout} 秒后超时")


class SimpleCache:
    """简单缓存"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        """设置缓存值"""
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[key] = (value, time.time())

    def _evict_oldest(self):
        """淘汰最旧的条目"""
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class ResourceOptimizer:
    """资源优化器"""

    @staticmethod
    def estimate_disk_needed(feature_count: int, avg_size_mb: float = 1.0) -> float:
        """估算需要的磁盘空间"""
        base = 50.0  # 基础开销
        feature_space = feature_count * avg_size_mb
        buffer = feature_space * 0.2  # 20% 缓冲
        return base + feature_space + buffer

    @staticmethod
    def get_optimal_batch_size(available_memory_mb: float, per_item_mb: float = 10) -> int:
        """获取最优批处理大小"""
        max_batch = int(available_memory_mb / per_item_mb)
        return max(1, min(max_batch, 100))  # 1-100 之间

    @staticmethod
    def suggest_backoff(retries: int, base_delay: float = 1.0) -> float:
        """建议退避延迟"""
        return base_delay * (2 ** retries)

    @staticmethod
    def clean_temporary_files(directory: str, age_hours: int = 24):
        """清理临时文件"""
        import shutil

        dir_path = Path(directory)
        if not dir_path.exists():
            return

        cutoff = time.time() - (age_hours * 3600)
        cleaned = 0
        space_freed = 0

        for item in dir_path.iterdir():
            if item.is_file() and item.stat().st_mtime < cutoff:
                try:
                    size = item.stat().st_size
                    item.unlink()
                    cleaned += 1
                    space_freed += size
                except Exception:
                    pass
            elif item.is_dir() and item.stat().st_mtime < cutoff:
                try:
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    shutil.rmtree(item)
                    cleaned += 1
                    space_freed += size
                except Exception:
                    pass

        return {
            "items_removed": cleaned,
            "space_freed_mb": space_freed / (1024 * 1024)
        }
