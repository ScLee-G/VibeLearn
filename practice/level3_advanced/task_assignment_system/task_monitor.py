from .base_agent import BaseAgent
from typing import Dict, Any, List


class TaskMonitor(BaseAgent):
    """任务监控 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("TaskMonitor", llm_client)
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """监控任务执行状态"""
        if not context or 'tasks' not in context:
            return {
                "status": "error",
                "message": "没有任务数据需要监控"
            }
        
        prompt = f"""
你是一个项目监控专家，请分析以下任务执行状态：

任务列表：{context['tasks']}

请按照以下格式输出监控报告：
{{
    "total_tasks": 总任务数,
    "completed_tasks": 已完成任务数,
    "in_progress_tasks": 进行中任务数,
    "failed_tasks": 失败任务数,
    "overall_progress": "完成百分比",
    "bottlenecks": ["瓶颈任务ID列表"],
    "risks": ["风险描述列表"],
    "recommendations": ["优化建议列表"],
    "summary": "监控总结"
}}
"""
        
        result = self.call_llm(prompt)
        return self._parse_result(result)
    
    def _parse_result(self, result: str) -> Dict[str, Any]:
        """解析 LLM 返回结果"""
        import json
        try:
            return json.loads(result)
        except:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "failed_tasks": 0,
                "overall_progress": "0%",
                "bottlenecks": [],
                "risks": [],
                "recommendations": [],
                "summary": result
            }
