from typing import Dict, Any, List
from .code_review_agent import CodeReviewAgent
from .security_agent import SecurityAgent
from .style_agent import StyleAgent
from .summarizer_agent import SummarizerAgent


class ReviewController:
    """多 Agent 代码审查控制器"""
    
    def __init__(self, llm_client=None):
        self.agents = [
            CodeReviewAgent(llm_client),
            SecurityAgent(llm_client),
            StyleAgent(llm_client)
        ]
        self.summarizer = SummarizerAgent(llm_client)
    
    def run_review(self, code: str) -> Dict[str, Any]:
        """执行完整的代码审查流程"""
        print("🚀 开始多 Agent 代码审查...")
        
        # 收集各 Agent 的审查结果
        results = {}
        for agent in self.agents:
            print(f"🔍 {agent.name} 正在审查...")
            result = agent.execute(code)
            results[agent.name] = result
        
        # 汇总结果
        print("📊 SummarizerAgent 正在汇总报告...")
        summary = self.summarizer.execute(code, results)
        
        return {
            "individual_results": results,
            "summary": summary
        }
    
    def run_review_parallel(self, code: str) -> Dict[str, Any]:
        """并行执行代码审查（模拟）"""
        import threading
        import queue
        
        print("🚀 开始并行多 Agent 代码审查...")
        
        results = {}
        result_queue = queue.Queue()
        
        def review_worker(agent, code, queue):
            result = agent.execute(code)
            queue.put((agent.name, result))
        
        threads = []
        for agent in self.agents:
            thread = threading.Thread(
                target=review_worker,
                args=(agent, code, result_queue)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        while not result_queue.empty():
            name, result = result_queue.get()
            results[name] = result
        
        print("📊 SummarizerAgent 正在汇总报告...")
        summary = self.summarizer.execute(code, results)
        
        return {
            "individual_results": results,
            "summary": summary
        }
