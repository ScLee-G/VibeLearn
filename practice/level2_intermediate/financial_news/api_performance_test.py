"""
AI模型API性能测试脚本
测试不同AI模型的响应时间和token用量
"""

import time
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """测试结果"""
    model_name: str
    provider: str
    response_time: float  # 秒
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    status: str
    error: Optional[str] = None


class APITester:
    """API性能测试器"""
    
    def __init__(self, test_prompt: str = None):
        self.test_prompt = test_prompt or "请简要介绍人工智能的主要应用场景，用200字以内回答。"
        self.results: List[TestResult] = []
        
        # API配置 - 从环境变量读取API密钥
        self.api_configs = {
            "openai": {
                "models": ["gpt-4o-mini", "gpt-4o"],
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": "https://api.openai.com/v1",
            },
            "anthropic": {
                "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "base_url": "https://api.anthropic.com",
            },
            "qwen": {
                "models": ["qwen-turbo", "qwen-plus"],
                "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            },
            "deepseek": {
                "models": ["deepseek-chat"],
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": "https://api.deepseek.com/v1",
            },
            "minimax": {
                "models": ["MiniMax-M1"],
                "api_key": os.getenv("MINIMAX_API_KEY", ""),
                "base_url": "https://api.minimax.chat/v1",
            },
        }
    
    def test_openai_model(self, model: str) -> TestResult:
        """测试OpenAI兼容的API"""
        try:
            from openai import OpenAI
            
            config = self.api_configs["openai"]
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": self.test_prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            response_time = time.time() - start_time
            
            return TestResult(
                model_name=model,
                provider="openai",
                response_time=response_time,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                status="success",
            )
        except Exception as e:
            return TestResult(
                model_name=model,
                provider="openai",
                response_time=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status="error",
                error=str(e),
            )
    
    def test_qwen_model(self, model: str) -> TestResult:
        """测试通义千问模型（使用OpenAI兼容接口）"""
        try:
            from openai import OpenAI
            
            config = self.api_configs["qwen"]
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": self.test_prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            response_time = time.time() - start_time
            
            return TestResult(
                model_name=model,
                provider="qwen",
                response_time=response_time,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                status="success",
            )
        except Exception as e:
            return TestResult(
                model_name=model,
                provider="qwen",
                response_time=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status="error",
                error=str(e),
            )
    
    def test_deepseek_model(self, model: str) -> TestResult:
        """测试DeepSeek模型（使用OpenAI兼容接口）"""
        try:
            from openai import OpenAI
            
            config = self.api_configs["deepseek"]
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": self.test_prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            response_time = time.time() - start_time
            
            return TestResult(
                model_name=model,
                provider="deepseek",
                response_time=response_time,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                status="success",
            )
        except Exception as e:
            return TestResult(
                model_name=model,
                provider="deepseek",
                response_time=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status="error",
                error=str(e),
            )
    
    def test_minimax_model(self, model: str) -> TestResult:
        """测试MiniMax模型"""
        try:
            from openai import OpenAI
            
            config = self.api_configs["minimax"]
            # MiniMax使用OpenAI兼容接口
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": self.test_prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            response_time = time.time() - start_time
            
            return TestResult(
                model_name=model,
                provider="minimax",
                response_time=response_time,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                status="success",
            )
        except Exception as e:
            return TestResult(
                model_name=model,
                provider="minimax",
                response_time=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status="error",
                error=str(e),
            )
    
    def run_all_tests(self, iterations: int = 3) -> List[TestResult]:
        """运行所有测试"""
        print("=" * 60)
        print("AI模型API性能测试")
        print("=" * 60)
        print(f"测试提示词：{self.test_prompt}")
        print(f"每个模型测试次数：{iterations}")
        print()
        
        all_results = []
        
        # 测试不同提供商的模型
        providers_tests = {
            "openai": self.test_openai_model,
            "qwen": self.test_qwen_model,
            "deepseek": self.test_deepseek_model,
            "minimax": self.test_minimax_model,
        }
        
        for provider, test_func in providers_tests.items():
            config = self.api_configs[provider]
            if not config["api_key"]:
                print(f"[跳过] {provider}: 未配置API密钥")
                continue
            
            print(f"\n{'='*40}")
            print(f"测试提供商：{provider}")
            print(f"{'='*40}")
            
            for model in config["models"]:
                print(f"\n测试模型：{model}")
                model_results = []
                
                for i in range(iterations):
                    print(f"  第 {i+1}/{iterations} 次测试...", end=" ")
                    result = test_func(model)
                    model_results.append(result)
                    all_results.append(result)
                    
                    if result.status == "success":
                        print(f"✅ {result.response_time:.2f}s | Tokens: {result.total_tokens}")
                    else:
                        print(f"❌ {result.error}")
                
                # 计算平均值
                successful = [r for r in model_results if r.status == "success"]
                if successful:
                    avg_time = sum(r.response_time for r in successful) / len(successful)
                    avg_tokens = sum(r.total_tokens for r in successful) / len(successful)
                    print(f"  平均：{avg_time:.2f}s | 平均Tokens: {avg_tokens:.0f}")
        
        self.results = all_results
        return all_results
    
    def print_summary(self):
        """打印测试摘要"""
        if not self.results:
            print("无测试结果")
            return
        
        successful = [r for r in self.results if r.status == "success"]
        if not successful:
            print("所有测试均失败")
            return
        
        # 按响应时间排序
        sorted_by_time = sorted(successful, key=lambda x: x.response_time)
        
        print("\n" + "=" * 60)
        print("测试结果摘要 - 按响应时间排序")
        print("=" * 60)
        
        print(f"\n{'排名':<4} {'模型':<25} {'提供商':<12} {'响应时间':<10} {'总Tokens':<10}")
        print("-" * 60)
        
        for i, result in enumerate(sorted_by_time, 1):
            print(f"{i:<4} {result.model_name:<25} {result.provider:<12} {result.response_time:<10.2f}s {result.total_tokens:<10}")
        
        # Token统计
        print("\n" + "=" * 60)
        print("Token用量统计")
        print("=" * 60)
        
        # 按模型分组统计
        model_stats = {}
        for r in successful:
            if r.model_name not in model_stats:
                model_stats[r.model_name] = {
                    "provider": r.provider,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_tokens": 0,
                    "count": 0,
                }
            model_stats[r.model_name]["total_prompt_tokens"] += r.prompt_tokens
            model_stats[r.model_name]["total_completion_tokens"] += r.completion_tokens
            model_stats[r.model_name]["total_tokens"] += r.total_tokens
            model_stats[r.model_name]["count"] += 1
        
        print(f"\n{'模型':<25} {'提供商':<12} {'平均输入':<12} {'平均输出':<12} {'平均总计':<12}")
        print("-" * 60)
        
        for model_name, stats in model_stats.items():
            avg_prompt = stats["total_prompt_tokens"] / stats["count"]
            avg_completion = stats["total_completion_tokens"] / stats["count"]
            avg_total = stats["total_tokens"] / stats["count"]
            print(f"{model_name:<25} {stats['provider']:<12} {avg_prompt:<12.0f} {avg_completion:<12.0f} {avg_total:<12.0f}")
    
    def save_results(self, filename: str = None):
        """保存测试结果到文件"""
        if not self.results:
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"
        
        results_data = []
        for r in self.results:
            results_data.append({
                "model_name": r.model_name,
                "provider": r.provider,
                "response_time": r.response_time,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "status": r.status,
                "error": r.error,
            })
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存至：{filename}")


def main():
    """主函数"""
    # 可选：自定义测试提示词
    test_prompt = "请简要介绍人工智能的主要应用场景，用200字以内回答。"
    
    tester = APITester(test_prompt=test_prompt)
    
    # 运行测试（每个模型测试3次）
    results = tester.run_all_tests(iterations=3)
    
    # 打印摘要
    tester.print_summary()
    
    # 保存结果
    tester.save_results()


if __name__ == "__main__":
    main()
