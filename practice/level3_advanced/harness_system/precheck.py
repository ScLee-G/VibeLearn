"""
Harness 系统 - 前置检查器

完整检查系统是否满足运行条件：
1. 系统资源检查
2. 网络连接检查
3. API可用性检查
4. 依赖安装检查
5. 配置验证检查
"""

import os
import sys
import json
import socket
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class CheckStatus(Enum):
    """检查状态"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = None
    suggestion: str = ""
    severity: int = 1  # 1=低, 2=中, 3=高


@dataclass
class Requirements:
    """需求规格"""
    name: str
    description: str
    required: bool = True
    suggested: Any = None


class SystemChecker:
    """系统前置检查器"""

    def __init__(self):
        self.results: List[CheckResult] = []
        self._MIN_PYTHON_VERSION = (3, 8)
        self._MIN_MEMORY_MB = 2048
        self._MIN_DISK_MB = 500
        self._MIN_CPU_CORES = 1
        self._SUGGESTED_MEMORY_MB = 8192
        self._SUGGESTED_DISK_MB = 2048
        self._REQUIRED_PACKAGES = ["openai"]

    def check_all(self) -> List[CheckResult]:
        """执行所有检查"""
        print("=" * 60)
        print("开始 Harness 系统前置检查")
        print("=" * 60)
        self.results = []

        # 系统基本信息
        self._check_python_version()
        self._check_system_resources()

        # 网络和连接
        self._check_network_connection()

        # 依赖
        self._check_required_packages()

        # API
        self._check_api_keys()
        self._test_api_connection()

        # 文件系统
        self._check_file_system()

        # 最后总结
        self._print_summary()

        return self.results

    def _print_summary(self):
        """打印检查总结"""
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASSED)
        warnings = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAILED)
        total = len(self.results)

        print("\n" + "=" * 60)
        print("检查总结")
        print("=" * 60)
        print(f"✅ 通过: {passed}/{total}")
        print(f"⚠️  警告: {warnings}/{total}")
        print(f"❌ 失败: {failed}/{total}")

        if failed > 0:
            print("\n请解决失败的检查后再运行 Harness 系统")

    def _check_python_version(self) -> CheckResult:
        """检查Python版本"""
        name = "Python 版本"
        current = sys.version_info
        try:
            if current >= self._MIN_PYTHON_VERSION:
                result = CheckResult(
                    name,
                    CheckStatus.PASSED,
                    f"Python {current.major}.{current.minor}.{current.micro}",
                    {
                        "current": f"{current.major}.{current.minor}.{current.micro}",
                        "minimum": f"{self._MIN_PYTHON_VERSION[0]}.{self._MIN_PYTHON_VERSION[1]}"
                    }
                )
            else:
                result = CheckResult(
                    name,
                    CheckStatus.FAILED,
                    f"Python {current.major}.{current.minor}.{current.micro}",
                    {
                        "current": f"{current.major}.{current.minor}.{current.micro}",
                        "minimum": f"{self._MIN_PYTHON_VERSION[0]}.{self._MIN_PYTHON_VERSION[1]}"
                    },
                    f"请升级 Python 到 {self._MIN_PYTHON_VERSION[0]}.{self._MIN_PYTHON_VERSION[1]}.x"
                )

            self.results.append(result)
            print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")
            return result
        except Exception as e:
            result = CheckResult(name, CheckStatus.FAILED, f"检查失败: {str(e)}")
            self.results.append(result)
            return result

    def _check_system_resources(self) -> List[CheckResult]:
        """检查系统资源"""
        import psutil

        results = []

        # 内存
        mem = psutil.virtual_memory()
        name = "内存"
        mem_mb = mem.total / (1024 * 1024)
        if mem_mb >= self._MIN_MEMORY_MB:
            status = CheckStatus.PASSED
            if mem_mb >= self._SUGGESTED_MEMORY_MB:
                msg = f"{mem_mb:.0f} MB"
            else:
                status = CheckStatus.WARNING
                msg = f"{mem_mb:.0f} MB (建议 {self._SUGGESTED_MEMORY_MB} MB)"
        else:
            status = CheckStatus.FAILED
            msg = f"{mem_mb:.0f} MB"
        mem_result = CheckResult(name, status, msg, {
                "current_mb": mem_mb,
                "minimum_mb": self._MIN_MEMORY_MB,
                "suggested_mb": self._SUGGESTED_MEMORY_MB
            })
        self.results.append(mem_result)
        results.append(mem_result)
        print(f"  {name}: {'✅' if status == CheckStatus.PASSED else '❌' if status == CheckStatus.FAILED else '⚠️'} {msg}")

        # CPU
        name = "CPU"
        cpu_cores = psutil.cpu_count()
        if cpu_cores >= self._MIN_CPU_CORES:
            status = CheckStatus.PASSED
            msg = f"{cpu_cores} 核心"
        else:
            status = CheckStatus.FAILED
            msg = f"{cpu_cores} 核心"
        cpu_result = CheckResult(name, status, msg, {
            "current": cpu_cores,
            "minimum": self._MIN_CPU_CORES
        })
        self.results.append(cpu_result)
        results.append(cpu_result)
        print(f"  {name}: {'✅' if status == CheckStatus.PASSED else '❌' if status == CheckStatus.FAILED else '⚠️'} {msg}")

        # 磁盘
        name = "磁盘空间"
        disk = psutil.disk_usage("/")
        disk_mb = disk.free / (1024 * 1024)
        if disk_mb >= self._MIN_DISK_MB:
            status = CheckStatus.PASSED
            if disk_mb >= self._SUGGESTED_DISK_MB:
                msg = f"{disk_mb:.0f} MB 可用"
            else:
                status = CheckStatus.WARNING
                msg = f"{disk_mb:.0f} MB 可用 (建议 {self._SUGGESTED_DISK_MB} MB)"
        else:
            status = CheckStatus.FAILED
            msg = f"{disk_mb:.0f} MB 可用"
        disk_result = CheckResult(name, status, msg, {
            "current_free_mb": disk_mb,
            "minimum_mb": self._MIN_DISK_MB,
            "suggested_mb": self._SUGGESTED_DISK_MB
        })
        self.results.append(disk_result)
        results.append(disk_result)
        print(f"  {name}: {'✅' if status == CheckStatus.PASSED else '❌' if status == CheckStatus.FAILED else '⚠️'} {msg}")

        return results

    def _check_network_connection(self) -> CheckResult:
        """检查网络连接"""
        name = "网络连接"
        try:
            # 尝试连接到常用DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)

            # 尝试连接到OpenAI API
            try:
                socket.create_connection(("api.openai.com", 443), timeout=3)
                result = CheckResult(
                    name,
                    CheckStatus.PASSED,
                    "网络连接正常"
                )
            except:
                result = CheckResult(
                    name,
                    CheckStatus.WARNING,
                    "可访问公网，但可能无法访问OpenAI API（视你的API提供商）",
                    suggestion="检查你的网络或使用代理"
                )
        except:
            result = CheckResult(
                name,
                CheckStatus.FAILED,
                "网络连接失败",
                suggestion="请检查网络连接"
            )
        self.results.append(result)
        print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")
        return result

    def _check_required_packages(self) -> List[CheckResult]:
        """检查必需的包"""
        checks = []

        for package in self._REQUIRED_PACKAGES:
            name = f"包: {package}"
            try:
                __import__(package)
                result = CheckResult(name, CheckStatus.PASSED, "已安装")
            except ImportError:
                result = CheckResult(
                    name,
                    CheckStatus.FAILED,
                    "未安装",
                    suggestion=f"运行: pip install {package}"
                )
            checks.append(result)
            self.results.append(result)
            print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")

        # 检查psutil
        name = "包: psutil"
        try:
            import psutil
            result = CheckResult(name, CheckStatus.PASSED, "已安装")
        except ImportError:
            result = CheckResult(
                name, CheckStatus.WARNING, "未安装（建议安装以启用资源监控",
                                   suggestion="运行: pip install psutil")
        checks.append(result)
        self.results.append(result)
        print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")

        return checks

    def _check_api_keys(self) -> CheckResult:
        """检查API密钥"""
        name = "API 密钥"
        key = os.getenv("OPENAI_API_KEY")
        has_key = key and len(key) > 10
        if has_key:
            result = CheckResult(name, CheckStatus.PASSED, "已设置")
        else:
            result = CheckResult(
                name,
                CheckStatus.FAILED,
                "未设置",
                suggestion="设置环境变量: export OPENAI_API_KEY=your_key"
            )
        self.results.append(result)
        print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")
        return result

    def _test_api_connection(self) -> CheckResult:
        """测试API连接"""
        name = "API 连通性测试"
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            result = CheckResult(
                name,
                CheckStatus.SKIPPED,
                "API密钥不存在，跳过测试",
                suggestion="设置API密钥后自动测试"
            )
            self.results.append(result)
            print(f"  {name}: ⏭️ {result.message}")
            return result

        # 尝试简单测试连接
        try:
            import openai
            from openai import OpenAI
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
            client = OpenAI(api_key=key, base_url=base_url)
            # 尝试列出模型（轻量请求）
            client.models.list()
            result = CheckResult(
                name,
                CheckStatus.PASSED,
                "API连接成功"
            )
        except Exception as e:
            result = CheckResult(
                name,
                CheckStatus.FAILED,
                f"API连接失败: {str(e)[:100]}",
                suggestion="检查API密钥和网络配置"
            )
        self.results.append(result)
        print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")
        return result

    def _check_file_system(self) -> CheckResult:
        """检查文件系统"""
        name = "文件系统权限"
        try:
            test_dir = Path("./harness_test")
            test_dir.mkdir(exist_ok=True)
            test_file = test_dir / "test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            test_dir.rmdir()
            result = CheckResult(name, CheckStatus.PASSED, "读写权限正常")
        except Exception as e:
            result = CheckResult(
                name,
                CheckStatus.FAILED,
                f"文件系统操作失败: {str(e)}",
                suggestion="检查当前目录权限"
            )
        self.results.append(result)
        print(f"  {name}: {'✅' if result.status == CheckStatus.PASSED else '❌' if result.status == CheckStatus.FAILED else '⚠️'} {result.message}")
        return result

    def can_run(self) -> bool:
        """是否可以运行"""
        if not self.results:
            return False
        critical_failed = any(
            r for r in self.results
            if r.status == CheckStatus.FAILED
            and r.severity >= 2
        )
        return not critical_failed

    def get_warnings(self) -> List[CheckResult]:
        """获取警告"""
        return [r for r in self.results if r.status == CheckStatus.WARNING]

    def get_failed(self) -> List[CheckResult]:
        """获取失败项"""
        return [r for r in self.results if r.status == CheckStatus.FAILED]

    def save_report(self, path: str):
        """保存检查报告"""
        report = {
            "timestamp": str(int(time.time())),
            "results": [
                {
                    **asdict(r),
                    "status": r.status.value
                }
                for r in self.results
            ],
            "can_run": self.can_run()
        }
        with open(path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def get_setup_guide():
    """获取设置指南"""
    return """
Harness 系统完整设置指南
============================

必需前置准备清单:

1. Python 3.8 或更高版本
2. 至少 2 GB RAM（推荐 8 GB 或更多）
3. 至少 500 MB 可用磁盘（推荐 2 GB）
4. 网络连接（公网）
5. OpenAI API Key
6. 已安装的 Python 包

快速安装:
    pip install openai psutil pandas

设置环境变量:
    Linux/Mac:
        export OPENAI_API_KEY="your-api-key-here"
        export OPENAI_BASE_URL="https://api.openai.com/v1"

    Windows (cmd:
        set OPENAI_API_KEY=your-api-key-here
        set OPENAI_BASE_URL=https://api.openai.com/v1
"""


if __name__ == "__main__":
    checker = SystemChecker()
    checker.check_all()
